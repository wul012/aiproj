"""Reusable preference data, DPO loss, training, and evaluation primitives."""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
import torch.nn.functional as F

from minigpt.model import MiniGPT
from minigpt.sft_corpus import EOS, OPS, SEP
from minigpt.sft_training import IGNORE_INDEX

LOG2 = math.log(2.0)


@dataclass
class PreferencePair:
    op: str
    reject_op: str
    prompt: str       # e.g. "Rabc="
    chosen: str        # gold completion incl EOS, e.g. "cba\n"
    rejected: str      # confusable other-op completion incl EOS, e.g. "abc\n"

    @property
    def chosen_text(self) -> str:
        return self.prompt + self.chosen

    @property
    def rejected_text(self) -> str:
        return self.prompt + self.rejected

    @property
    def n_prompt(self) -> int:
        return len(self.prompt)

    @property
    def chosen_output(self) -> str:
        return self.chosen[: -len(EOS)] if self.chosen.endswith(EOS) else self.chosen

    @property
    def rejected_output(self) -> str:
        return self.rejected[: -len(EOS)] if self.rejected.endswith(EOS) else self.rejected


def build_confusable_preferences(examples, ops) -> tuple[list[PreferencePair], int]:
    """Turn SFT examples into (chosen, rejected) preference pairs.

    The rejected completion is the output of the cyclically-next op on the SAME
    input -- a plausible instruction-confusion error. Degenerate pairs where the
    confusable op happens to produce the SAME string (reverse of a palindrome,
    sort of an already-sorted string, any op on "aaa", ...) are DROPPED and
    counted, because a chosen==rejected pair gives an identically-zero DPO
    gradient and would silently dilute the dataset. Returns (pairs, dropped).
    """
    ops = tuple(ops)
    if len(ops) < 2:
        raise ValueError("need at least two ops to build confusable negatives")
    pairs: list[PreferencePair] = []
    dropped = 0
    for e in examples:
        idx = ops.index(e.op)
        reject_op = ops[(idx + 1) % len(ops)]
        input_str = e.prompt[len(e.op): -len(SEP)]
        rejected = OPS[reject_op](input_str) + EOS
        if rejected == e.completion:
            dropped += 1
            continue
        pairs.append(PreferencePair(op=e.op, reject_op=reject_op, prompt=e.prompt, chosen=e.completion, rejected=rejected))
    return pairs, dropped


# ----------------------------------------------------------------------------
# DPO core: per-sequence completion log-prob, the loss, and the training loop.
# ----------------------------------------------------------------------------


def logp_completion(
    model: MiniGPT,
    examples: list[tuple[list[int], int]],
    pad_id: int,
    *,
    device: torch.device,
    ignore_index: int = IGNORE_INDEX,
) -> torch.Tensor:
    """Per-sequence SUMMED log-prob of the completion tokens.

    ``examples`` is ``(full_ids, n_prompt)`` (prompt followed by completion, no
    padding inside ``full_ids``). The supervised set is EXACTLY the one
    :func:`minigpt.sft_training.train_sft` builds: target position ``t`` (which
    predicts ``full[t+1]``) counts iff ``(t+1) >= n_prompt`` -- the completion,
    including its EOS. Returns a ``(B,)`` tensor; differentiable when ``model``
    is in train mode and not under ``no_grad``. Trailing padding is masked and,
    being causal, does not affect earlier positions, so the result is invariant
    to batch padding width.
    """
    n = len(examples)
    if n == 0:
        raise ValueError("no examples for logp_completion")
    max_len = max(len(full) for full, _ in examples)
    width = max_len - 1
    X = torch.full((n, width), pad_id, dtype=torch.long)
    labels = torch.full((n, width), ignore_index, dtype=torch.long)
    for i, (full, n_prompt) in enumerate(examples):
        inp, tgt = full[:-1], full[1:]
        X[i, : len(inp)] = torch.tensor(inp, dtype=torch.long)
        for t, tok in enumerate(tgt):
            if (t + 1) >= n_prompt:
                labels[i, t] = tok
    X = X.to(device)
    labels = labels.to(device)
    logits, _ = model(X)
    logp = F.log_softmax(logits, dim=-1)
    mask = labels != ignore_index
    gathered = logp.gather(-1, labels.clamp(min=0).unsqueeze(-1)).squeeze(-1)
    return (gathered * mask).sum(dim=1)


def dpo_loss(
    policy_chosen: torch.Tensor,
    policy_rejected: torch.Tensor,
    ref_chosen: torch.Tensor,
    ref_rejected: torch.Tensor,
    beta: float,
    *,
    use_reference: bool = True,
) -> torch.Tensor:
    """The DPO loss. With ``use_reference`` the implicit reward is anchored to a
    frozen reference (margin_ref subtracted); without it the objective is the
    unanchored ``beta * margin_theta`` (the ablation arm). ``ref_*`` must be
    detached / computed under ``no_grad``."""
    policy_margin = policy_chosen - policy_rejected
    if use_reference:
        ref_margin = ref_chosen - ref_rejected
        logits = beta * (policy_margin - ref_margin)
    else:
        logits = beta * policy_margin
    return -F.logsigmoid(logits).mean()


def train_dpo(
    policy: MiniGPT,
    ref: MiniGPT | None,
    triples: list[tuple[list[int], int, list[int], int]],
    *,
    steps: int,
    lr: float,
    beta: float,
    batch_size: int,
    device: torch.device,
    pad_id: int,
    use_reference: bool = True,
    weight_decay: float | None = None,
    log_every: int | None = None,
    label: str = "dpo",
) -> float:
    """Train ``policy`` with the DPO loss and return the last batch loss.

    Each triple is ``(chosen_full, n_prompt_c, rejected_full, n_prompt_r)``. The
    reference's log-probs are constant (it is frozen), so they are precomputed
    once and indexed per batch. With ``use_reference=False`` (or ``ref=None``)
    the reference term is dropped -- the only difference between the with-ref and
    no-ref arms, which otherwise share init and batch stream.
    """
    n = len(triples)
    if n == 0:
        raise ValueError("no preference triples to train on")
    chosen = [(c, npc) for c, npc, _r, _npr in triples]
    rejected = [(r, npr) for _c, _npc, r, npr in triples]

    use_ref = use_reference and ref is not None
    ref_chosen_all = ref_rejected_all = None
    if use_ref:
        ref.eval()
        with torch.no_grad():
            ref_chosen_all = logp_completion(ref, chosen, pad_id, device=device)
            ref_rejected_all = logp_completion(ref, rejected, pad_id, device=device)

    optimizer = (
        torch.optim.AdamW(policy.parameters(), lr=lr)
        if weight_decay is None
        else torch.optim.AdamW(policy.parameters(), lr=lr, weight_decay=weight_decay)
    )
    policy.train()
    last = float("nan")
    for step in range(1, steps + 1):
        sel = torch.randint(0, n, (batch_size,), device=device)
        sel_list = sel.tolist()
        batch_chosen = [chosen[i] for i in sel_list]
        batch_rejected = [rejected[i] for i in sel_list]
        pol_c = logp_completion(policy, batch_chosen, pad_id, device=device)
        pol_r = logp_completion(policy, batch_rejected, pad_id, device=device)
        if use_ref:
            ref_c = ref_chosen_all[sel]
            ref_r = ref_rejected_all[sel]
        else:
            ref_c = torch.zeros_like(pol_c)
            ref_r = torch.zeros_like(pol_r)
        loss = dpo_loss(pol_c, pol_r, ref_c, ref_r, beta, use_reference=use_ref)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        last = float(loss.item())
        if log_every and (step == 1 or step % log_every == 0 or step == steps):
            print(f"[{label}] step={step:5d} loss={last:.4f}")
    return last


# ----------------------------------------------------------------------------
# Evaluation: the optimization-target diagnostic and the capability headline.
# ----------------------------------------------------------------------------


@torch.no_grad()
def evaluate_preference(
    model: MiniGPT,
    eval_triples: list[tuple[list[int], int, list[int], int]],
    pad_id: int,
    *,
    device: torch.device,
) -> dict[str, object]:
    """Margin-side metrics on held-out triples: preference accuracy and the
    absolute chosen/rejected log-probs (the only way to see the pathology where
    the margin rises because logp_chosen drops)."""
    was_training = model.training
    model.eval()
    chosen = [(c, npc) for c, npc, _r, _npr in eval_triples]
    rejected = [(r, npr) for _c, _npc, r, npr in eval_triples]
    lc = logp_completion(model, chosen, pad_id, device=device)
    lr = logp_completion(model, rejected, pad_id, device=device)
    margin = lc - lr
    if was_training:
        model.train()
    return {
        "preference_accuracy": float((margin > 0).float().mean().item()),
        "mean_logp_chosen": float(lc.mean().item()),
        "mean_logp_rejected": float(lr.mean().item()),
        "mean_margin": float(margin.mean().item()),
        "logp_chosen_vec": lc.detach().cpu(),
    }


@torch.no_grad()
def evaluate_confusable(
    model: MiniGPT,
    items: list[tuple[list[int], list[int], list[int], str]],
    *,
    eos_id: int,
    max_new_tokens: int,
    device: torch.device,
) -> dict[str, object]:
    """Fraction of held-out prompts whose greedy generation equals the REJECTED
    (confusable other-op) output -- the specific error framing C hoped DPO would
    suppress. ``items`` is ``(prompt_ids, expected_ids, rejected_ids, op)``."""
    was_training = model.training
    model.eval()
    groups: dict[int, list[tuple[list[int], list[int], list[int], str]]] = {}
    for item in items:
        groups.setdefault(len(item[0]), []).append(item)
    per_op: dict[str, list[int]] = {}
    confusable = 0
    total = 0
    for plen, group in groups.items():
        idx = torch.tensor([p for p, _, _, _ in group], dtype=torch.long, device=device)
        out = model.generate(idx, max_new_tokens=max_new_tokens, top_k=1)
        for row, (_, _expected, rejected, op) in zip(out[:, plen:].tolist(), group):
            if eos_id in row:
                row = row[: row.index(eos_id)]
            hit = int(row == list(rejected))
            slot = per_op.setdefault(op, [0, 0])
            slot[0] += hit
            slot[1] += 1
            confusable += hit
            total += 1
    if was_training:
        model.train()
    return {
        "confusable_error_rate": confusable / total if total else 0.0,
        "by_op": {op: c / t for op, (c, t) in per_op.items()},
        "count": total,
    }
__all__ = [
    "LOG2",
    "PreferencePair",
    "build_confusable_preferences",
    "logp_completion",
    "dpo_loss",
    "train_dpo",
    "evaluate_preference",
    "evaluate_confusable",
]

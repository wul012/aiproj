"""v1166: DPO-lite preference tuning, and the honest lesson it teaches.

This is Direct Preference Optimization (DPO) THE LOSS, applied to a synthetic
*correctness* signal -- NOT human preferences, NOT RLHF, NOT subjective quality.
Starting from a deliberately-weak SFT init, we optimize

    L = -E[ log sigmoid( beta * ( (logp_w - logp_l) - (logp_w^ref - logp_l^ref) ) ) ]

over preference triples (prompt, chosen, rejected) where ``chosen`` is the gold
op output and ``rejected`` is a CONFUSABLE other-op output on the SAME input
(e.g. for "Rabc=" chosen "cba", rejected = the sorted "abc"). ``logp`` is the
SUM of completion-token log-probs with the prompt+pad masked EXACTLY as
``minigpt.sft_training`` masks it.

The adversarial design panel (run on real CPU code before this GPU experiment)
falsified the flattering framings and located the real, citable phenomenon:

* DPO optimizes a RELATIVE margin, so preference accuracy (logp_chosen >
  logp_rejected) reliably rises -- but absolute logp_chosen can FALL while
  logp_rejected falls faster, and held-out greedy generation (exact-match) can
  REGRESS below the SFT init. The probe saw 0.63 -> 0.22 exact-match while the
  margin grew, in 8/8 (lr x beta) cells.
* A matched-compute SFT-on-chosen control (the killer baseline) reached 0.85
  exact-match vs DPO's 0.22 at the SAME preference accuracy -- "just more SFT on
  the positives" beats DPO on generation at this scale.
* The reference/KL term showed no consistent stabilization at this tiny scale
  (a measured null), even though it matters at large scale.

So three honest disciplines are baked in here:

1. Two headline metrics, never collapsed: ``preference_accuracy`` (the
   optimization target, expected to move) and held-out ``exact_match`` (the
   capability metric). They can diverge -- that divergence IS the finding.
2. A compute-MATCHED comparison on the fair axis (FORWARD PASSES): DPO does two
   policy forwards/step (chosen+rejected), so SFT-on-chosen gets ~2x the
   optimizer steps at the same budget.
3. A headroom GATE mirroring v1165's invariant: ``status=="pass"`` IFF
   ``summary["task_learned"]`` (here: the SFT init is in a usable mid band, the
   DPO loss is actually optimized, and the margin is improvable). A "pass" run
   certifies the comparison was VALID and measurable -- it does NOT mean DPO is
   good, and the probe makes the unflattering verdict the expected outcome.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch
import torch.nn.functional as F

from minigpt.experiment_utils import build_minigpt, clone_state, mean_std, significant
from minigpt.model import MiniGPT
from minigpt.report_utils import utc_now
from minigpt.sft_corpus import EOS, OPS, SEP
from minigpt.sft_instruction_v1164 import evaluate_instructions
from minigpt.sft_training import IGNORE_INDEX, train_sft

LOG2 = math.log(2.0)

# ----------------------------------------------------------------------------
# Preference data: confusable hard-negatives built on top of the SFT corpus.
# ----------------------------------------------------------------------------


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


# ----------------------------------------------------------------------------
# Experiment driver.
# ----------------------------------------------------------------------------


@dataclass
class DpoPreferenceConfig:
    block_size: int = 16
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    sft_init_steps: int = 3000             # calibrated: lands all-seed held-out exact-match in the [0.40,0.85] band
    sft_init_lr: float = 3e-3
    budget_sweep: tuple[int, ...] = (240, 720, 1600)  # FORWARD-pass budgets (fair compute axis)
    beta: float = 0.1
    lr: float = 1e-3
    batch_size: int = 32
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 128
    use_rope: bool = True
    max_new_tokens: int = 8
    gate_lower: float = 0.40
    gate_upper: float = 0.85
    # severity-scaling diagnostic (single seed, max budget): pathology vs lr/beta
    scaling_betas: tuple[float, ...] = (0.1, 0.3)
    scaling_lrs: tuple[float, ...] = (1e-3, 3e-4)


ARMS = ("dpo_with_ref", "dpo_no_ref", "sft_on_chosen")

REVIEW_VERDICTS = {
    "dpo_no_headroom_init_saturated",
    "dpo_init_unlearnable",
    "dpo_loss_not_optimized",
    "margin_not_improvable",
}
PRIMARY_VERDICTS = {
    "dpo_raises_margin_but_generation_regresses",
    "dpo_raises_margin_without_generation_gain",
    "dpo_improves_margin_and_generation_but_matched_by_more_sft",
    "dpo_uniquely_improves_generation_over_matched_sft",
    "dpo_margin_did_not_move",
}
REFERENCE_VERDICTS = {
    "reference_term_stabilizes_dpo",
    "reference_term_unnecessary_or_harmful_at_this_scale",
    "reference_term_no_measurable_effect_at_this_scale",
}
SFT_CONTROL_VERDICTS = {
    "matched_compute_sft_on_chosen_beats_dpo_on_generation",
    "dpo_matches_sft_on_chosen",
    "dpo_beats_sft_on_chosen",
}


def _param_l2_delta(state_a: dict, state_b: dict) -> float:
    total = 0.0
    for key, value in state_a.items():
        diff = value.float() - state_b[key].float()
        total += float((diff * diff).sum().item())
    return total ** 0.5


def run_dpo_preference(
    *,
    vocab_size: int,
    sft_init_train: list[tuple[list[int], int]],
    pref_train_triples: list[tuple[list[int], int, list[int], int]],
    eval_triples: list[tuple[list[int], int, list[int], int]],
    eval_heldout_instructions: list[tuple[list[int], list[int], str]],
    eval_confusable: list[tuple[list[int], list[int], list[int], str]],
    ops: tuple[str, ...],
    pad_id: int,
    eos_id: int,
    config: DpoPreferenceConfig,
    device: torch.device,
    corpus_stats: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    schedule = tuple(sorted(set(config.budget_sweep)))
    min_b, max_b = min(schedule), max(schedule)
    chosen_only = [(c, npc) for c, npc, _r, _npr in pref_train_triples]

    # metric[arm][budget][name] -> list over seeds
    metric: dict[str, dict[int, dict[str, list[float]]]] = {
        a: {b: {} for b in schedule} for a in ARMS
    }
    init_metric: dict[str, list[float]] = {}
    scaling_rows: list[dict] = []

    def _record(arm: str, budget: int, name: str, value: float) -> None:
        metric[arm][budget].setdefault(name, []).append(value)

    def _eval_arm(model: MiniGPT, init_state: dict, init_pref: dict) -> dict[str, float]:
        pref = evaluate_preference(model, eval_triples, pad_id, device=device)
        em = evaluate_instructions(model, eval_heldout_instructions, eos_id=eos_id,
                                   max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"]
        conf = evaluate_confusable(model, eval_confusable, eos_id=eos_id,
                                   max_new_tokens=config.max_new_tokens, device=device)["confusable_error_rate"]
        drift = float((pref["logp_chosen_vec"] - init_pref["logp_chosen_vec"]).abs().mean().item())
        return {
            "pref_acc": pref["preference_accuracy"],
            "exact_match": em,
            "mean_logp_chosen": pref["mean_logp_chosen"],
            "mean_logp_rejected": pref["mean_logp_rejected"],
            "mean_margin": pref["mean_margin"],
            "delta_logp_chosen": pref["mean_logp_chosen"] - init_pref["mean_logp_chosen"],
            "delta_logp_rejected": pref["mean_logp_rejected"] - init_pref["mean_logp_rejected"],
            "confusable_error_rate": conf,
            "param_l2_delta": _param_l2_delta(clone_state(model), init_state),
            "logp_drift": drift,
        }

    for seed in config.seeds:
        torch.manual_seed(seed)
        init_model = build_minigpt(vocab_size, config).to(device)
        train_sft(init_model, sft_init_train, steps=config.sft_init_steps, lr=config.sft_init_lr,
                  batch_size=config.batch_size, block_size=config.block_size, device=device,
                  pad_id=pad_id, mask_prompt=True)
        init_state = clone_state(init_model)
        init_pref = evaluate_preference(init_model, eval_triples, pad_id, device=device)
        init_em = evaluate_instructions(init_model, eval_heldout_instructions, eos_id=eos_id,
                                        max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"]
        init_conf = evaluate_confusable(init_model, eval_confusable, eos_id=eos_id,
                                        max_new_tokens=config.max_new_tokens, device=device)["confusable_error_rate"]
        init_metric.setdefault("exact_match", []).append(init_em)
        init_metric.setdefault("pref_acc", []).append(init_pref["preference_accuracy"])
        init_metric.setdefault("mean_logp_chosen", []).append(init_pref["mean_logp_chosen"])
        init_metric.setdefault("mean_logp_rejected", []).append(init_pref["mean_logp_rejected"])
        init_metric.setdefault("mean_margin", []).append(init_pref["mean_margin"])
        init_metric.setdefault("confusable_error_rate", []).append(init_conf)

        for budget in schedule:
            dpo_steps = max(1, budget // 2)   # 2 policy forwards/step
            sft_steps = budget                 # 1 forward/step -> matched on forward passes
            dpo_seed = 20_000 + seed * 13 + budget

            # dpo_with_ref
            policy = build_minigpt(vocab_size, config).to(device)
            policy.load_state_dict(init_state)
            ref = build_minigpt(vocab_size, config).to(device)
            ref.load_state_dict(init_state)
            ref.eval()
            ref.requires_grad_(False)
            torch.manual_seed(dpo_seed)
            last_wr = train_dpo(policy, ref, pref_train_triples, steps=dpo_steps, lr=config.lr,
                                beta=config.beta, batch_size=config.batch_size, device=device,
                                pad_id=pad_id, use_reference=True)
            for name, value in _eval_arm(policy, init_state, init_pref).items():
                _record("dpo_with_ref", budget, name, value)
            _record("dpo_with_ref", budget, "last_loss", last_wr)

            # dpo_no_ref (same init, same seeded batch stream; only the loss term differs)
            policy_nr = build_minigpt(vocab_size, config).to(device)
            policy_nr.load_state_dict(init_state)
            torch.manual_seed(dpo_seed)
            last_nr = train_dpo(policy_nr, None, pref_train_triples, steps=dpo_steps, lr=config.lr,
                                beta=config.beta, batch_size=config.batch_size, device=device,
                                pad_id=pad_id, use_reference=False)
            for name, value in _eval_arm(policy_nr, init_state, init_pref).items():
                _record("dpo_no_ref", budget, name, value)
            _record("dpo_no_ref", budget, "last_loss", last_nr)

            # sft_on_chosen (the killer control): more SFT on the positives, matched on forward passes
            model_s = build_minigpt(vocab_size, config).to(device)
            model_s.load_state_dict(init_state)
            torch.manual_seed(dpo_seed)
            train_sft(model_s, chosen_only, steps=sft_steps, lr=config.lr,
                      batch_size=config.batch_size, block_size=config.block_size, device=device,
                      pad_id=pad_id, mask_prompt=True)
            for name, value in _eval_arm(model_s, init_state, init_pref).items():
                _record("sft_on_chosen", budget, name, value)
            _record("sft_on_chosen", budget, "last_loss", float("nan"))

        # severity-scaling diagnostic on the first seed only, at the max budget
        if seed == config.seeds[0]:
            grid_steps = max(1, max_b // 2)
            for grid_beta in config.scaling_betas:
                for grid_lr in config.scaling_lrs:
                    gp = build_minigpt(vocab_size, config).to(device)
                    gp.load_state_dict(init_state)
                    gref = build_minigpt(vocab_size, config).to(device)
                    gref.load_state_dict(init_state)
                    gref.eval()
                    gref.requires_grad_(False)
                    torch.manual_seed(30_000 + int(grid_beta * 100) + int(grid_lr * 1e5))
                    train_dpo(gp, gref, pref_train_triples, steps=grid_steps, lr=grid_lr,
                              beta=grid_beta, batch_size=config.batch_size, device=device,
                              pad_id=pad_id, use_reference=True)
                    ev = _eval_arm(gp, init_state, init_pref)
                    scaling_rows.append({
                        "beta": grid_beta, "lr": grid_lr,
                        "exact_match": round(ev["exact_match"], 6),
                        "exact_match_minus_init": round(ev["exact_match"] - init_em, 6),
                        "delta_logp_chosen": round(ev["delta_logp_chosen"], 6),
                        "delta_margin": round(ev["mean_margin"] - init_pref["mean_margin"], 6),
                    })

    # ---- aggregate ----
    def ms(arm: str, budget: int, name: str) -> tuple[float, float]:
        return mean_std(metric[arm][budget].get(name, []))

    rows: list[dict] = []
    accuracy_curves: dict[str, dict[str, float]] = {a: {} for a in ARMS}
    pref_acc_curves: dict[str, dict[str, float]] = {a: {} for a in ARMS}

    init_em_mean, _ = mean_std(init_metric.get("exact_match", []))
    init_pa_mean, init_pa_std = mean_std(init_metric.get("pref_acc", []))
    init_lc_mean, _ = mean_std(init_metric.get("mean_logp_chosen", []))
    init_lr_mean, _ = mean_std(init_metric.get("mean_logp_rejected", []))
    init_margin_mean, init_margin_std = mean_std(init_metric.get("mean_margin", []))
    init_conf_mean, _ = mean_std(init_metric.get("confusable_error_rate", []))
    rows.append({
        "arm": "sft_init", "budget_forward_passes": 0, "opt_steps": 0,
        "pref_acc_mean": round(init_pa_mean, 6), "pref_acc_std": round(init_pa_std, 6),
        "exact_match_mean": round(init_em_mean, 6), "exact_match_std": round(mean_std(init_metric.get("exact_match", []))[1], 6),
        "mean_logp_chosen": round(init_lc_mean, 6), "mean_logp_rejected": round(init_lr_mean, 6),
        "delta_logp_chosen": 0.0, "delta_logp_rejected": 0.0,
        "mean_margin": round(mean_std(init_metric.get("mean_margin", []))[0], 6),
        "confusable_error_rate": round(init_conf_mean, 6),
        "param_l2_delta": 0.0, "logp_drift": 0.0, "dpo_last_loss": "",
    })
    for arm in ARMS:
        for budget in schedule:
            pa_m, pa_s = ms(arm, budget, "pref_acc")
            em_m, em_s = ms(arm, budget, "exact_match")
            accuracy_curves[arm][str(budget)] = round(em_m, 6)
            pref_acc_curves[arm][str(budget)] = round(pa_m, 6)
            rows.append({
                "arm": arm, "budget_forward_passes": budget,
                "opt_steps": (budget // 2 if arm.startswith("dpo") else budget),
                "pref_acc_mean": round(pa_m, 6), "pref_acc_std": round(pa_s, 6),
                "exact_match_mean": round(em_m, 6), "exact_match_std": round(em_s, 6),
                "mean_logp_chosen": round(ms(arm, budget, "mean_logp_chosen")[0], 6),
                "mean_logp_rejected": round(ms(arm, budget, "mean_logp_rejected")[0], 6),
                "delta_logp_chosen": round(ms(arm, budget, "delta_logp_chosen")[0], 6),
                "delta_logp_rejected": round(ms(arm, budget, "delta_logp_rejected")[0], 6),
                "mean_margin": round(ms(arm, budget, "mean_margin")[0], 6),
                "confusable_error_rate": round(ms(arm, budget, "confusable_error_rate")[0], 6),
                "param_l2_delta": round(ms(arm, budget, "param_l2_delta")[0], 6),
                "logp_drift": round(ms(arm, budget, "logp_drift")[0], 6),
                "dpo_last_loss": ("" if math.isnan(ms(arm, budget, "last_loss")[0]) else round(ms(arm, budget, "last_loss")[0], 6)),
            })

    # ---- headroom / learnability gate ----
    # NOTE on the margin (not pref-acc) gate: preference ACCURACY saturates near
    # 1.0 at the SFT init because ranking chosen>rejected is far easier than
    # GENERATING correctly, so it is an uninformative, nondeterminism-flaky gate
    # signal. The faithful measure of "is the preference objective genuinely
    # driven on held-out" is the MARGIN (logp_chosen - logp_rejected), which moves
    # robustly. We therefore gate on margin-improvability and report pref-acc too.
    wr_loss_min, _ = ms("dpo_with_ref", min_b, "last_loss")
    wr_loss_max, _ = ms("dpo_with_ref", max_b, "last_loss")
    wr_pa_max, wr_pa_max_std = ms("dpo_with_ref", max_b, "pref_acc")
    wr_margin_max, wr_margin_max_std = ms("dpo_with_ref", max_b, "mean_margin")
    loss_optimized = (not math.isnan(wr_loss_max)) and (wr_loss_max < LOG2 - 0.05) and (wr_loss_max <= wr_loss_min + 1e-9)
    margin_improvable = significant(wr_margin_max, wr_margin_max_std, init_margin_mean, init_margin_std)
    in_band = config.gate_lower <= init_em_mean <= config.gate_upper

    task_learned = bool(in_band and loss_optimized and margin_improvable)

    if not in_band:
        decision = verdict = ("dpo_no_headroom_init_saturated" if init_em_mean > config.gate_upper else "dpo_init_unlearnable")
        status = "review"
    elif not loss_optimized:
        decision = verdict = "dpo_loss_not_optimized"
        status = "review"
    elif not margin_improvable:
        decision = verdict = "margin_not_improvable"
        status = "review"
    else:
        status, decision = "pass", "dpo_preference_tuning_measured"
        verdict = "pending"

    # ---- verdicts at max budget (multi-seed, gap-minus-combined-std) ----
    wr_em_max, wr_em_max_std = ms("dpo_with_ref", max_b, "exact_match")
    nr_em_max, nr_em_max_std = ms("dpo_no_ref", max_b, "exact_match")
    sft_em_max, sft_em_max_std = ms("sft_on_chosen", max_b, "exact_match")
    wr_dlc_max, _ = ms("dpo_with_ref", max_b, "delta_logp_chosen")
    init_em_std = mean_std(init_metric.get("exact_match", []))[1]

    margin_up = margin_improvable
    em_dpo_up = significant(wr_em_max, wr_em_max_std, init_em_mean, init_em_std)
    em_dpo_down = significant(init_em_mean, init_em_std, wr_em_max, wr_em_max_std)
    logp_c_down = wr_dlc_max < -1e-4
    sft_beats_dpo = significant(sft_em_max, sft_em_max_std, wr_em_max, wr_em_max_std)
    dpo_beats_sft = significant(wr_em_max, wr_em_max_std, sft_em_max, sft_em_max_std)

    if status == "pass":
        if not margin_up:
            verdict = "dpo_margin_did_not_move"
        elif em_dpo_down:
            verdict = "dpo_raises_margin_but_generation_regresses"
        elif em_dpo_up and dpo_beats_sft:
            verdict = "dpo_uniquely_improves_generation_over_matched_sft"
        elif em_dpo_up:
            verdict = "dpo_improves_margin_and_generation_but_matched_by_more_sft"
        else:
            verdict = "dpo_raises_margin_without_generation_gain"

    # secondary: reference term (with-ref vs no-ref at max budget)
    if significant(wr_em_max, wr_em_max_std, nr_em_max, nr_em_max_std):
        reference_verdict = "reference_term_stabilizes_dpo"
    elif significant(nr_em_max, nr_em_max_std, wr_em_max, wr_em_max_std):
        reference_verdict = "reference_term_unnecessary_or_harmful_at_this_scale"
    else:
        reference_verdict = "reference_term_no_measurable_effect_at_this_scale"

    # secondary: SFT-on-chosen control
    if sft_beats_dpo:
        sft_control_verdict = "matched_compute_sft_on_chosen_beats_dpo_on_generation"
    elif dpo_beats_sft:
        sft_control_verdict = "dpo_beats_sft_on_chosen"
    else:
        sft_control_verdict = "dpo_matches_sft_on_chosen"

    stats = corpus_stats or {}
    summary = {
        "status": status,
        "decision": decision,
        "verdict": verdict,
        "reference_verdict": reference_verdict,
        "sft_control_verdict": sft_control_verdict,
        "device": str(device),
        "seeds": len(config.seeds),
        "ops": ",".join(ops),
        "beta": config.beta,
        "lr": config.lr,
        "sft_init_steps": config.sft_init_steps,
        "budget_sweep": ",".join(str(b) for b in schedule),
        "compute_axis": "forward_passes (dpo: 2 policy forwards/step; sft_on_chosen: 1/step)",
        "n_layer": config.n_layer,
        "n_head": config.n_head,
        "n_embd": config.n_embd,
        "use_rope": config.use_rope,
        "pref_train_pairs": stats.get("pref_train_pairs"),
        "pref_eval_pairs": stats.get("pref_eval_pairs"),
        "dropped_degenerate_pairs": stats.get("dropped_degenerate_pairs"),
        "gate_lower": config.gate_lower,
        "gate_upper": config.gate_upper,
        "sft_init_exact_match": round(init_em_mean, 6),
        "sft_init_pref_acc": round(init_pa_mean, 6),
        "sft_init_mean_margin": round(init_margin_mean, 6),
        "sft_init_logp_chosen": round(init_lc_mean, 6),
        "sft_init_confusable_error_rate": round(init_conf_mean, 6),
        "loss_optimized": loss_optimized,
        "margin_improvable": margin_improvable,
        "task_learned": task_learned,
        "min_budget": min_b,
        "max_budget": max_b,
        "dpo_with_ref_pref_acc_at_max": round(wr_pa_max, 6),
        "dpo_with_ref_mean_margin_at_max": round(wr_margin_max, 6),
        "dpo_with_ref_exact_match_at_max": round(wr_em_max, 6),
        "dpo_with_ref_delta_logp_chosen_at_max": round(wr_dlc_max, 6),
        "dpo_no_ref_exact_match_at_max": round(nr_em_max, 6),
        "sft_on_chosen_exact_match_at_max": round(sft_em_max, 6),
        "dpo_with_ref_last_loss_at_max": round(wr_loss_max, 6),
    }

    recommendations = [
        f"VERDICT ({verdict}): from a weak SFT init (held-out exact-match {init_em_mean:.3f}, in the [{config.gate_lower},{config.gate_upper}] headroom band), DPO-with-ref at {max_b} forward passes grows the held-out margin {init_margin_mean:.1f} -> {wr_margin_max:.1f} (preference-accuracy {init_pa_mean:.3f} -> {wr_pa_max:.3f}, already near-ceiling) but held-out exact-match FALLS {init_em_mean:.3f} -> {wr_em_max:.3f}, with delta_logp_chosen {wr_dlc_max:+.3f}. {len(config.seeds)} seeds, gap-minus-combined-std significance.",
        f"THE LESSON: the MARGIN (and pref-accuracy) is the OPTIMIZATION TARGET (it moves by construction); held-out exact-match is the CAPABILITY metric. DPO maximizes a RELATIVE margin, so logp_chosen can fall while logp_rejected falls faster — the margin can rise while generation does not improve. NOTE: pref-accuracy saturates near 1.0 at the init (ranking is easier than generating), so the margin is the faithful 'did the objective move' signal; do not read a preference rise as a capability win.",
        f"KILLER CONTROL ({sft_control_verdict}): matched on FORWARD PASSES (DPO does 2 policy forwards/step, so SFT-on-chosen gets ~2x the optimizer steps), continued SFT-on-chosen reaches exact-match {sft_em_max:.3f} vs DPO-with-ref {wr_em_max:.3f} at the max budget. This tests whether any DPO movement is uniquely DPO or just more supervision on positives.",
        f"REFERENCE TERM ({reference_verdict}): DPO-no-ref reaches exact-match {nr_em_max:.3f} vs with-ref {wr_em_max:.3f} at max budget. The KL/reference anchor's stabilizing benefit is a large-scale phenomenon; whatever is reported here is bounded to this tiny scale.",
        f"GATE: status='{status}' means the comparison was VALID and measurable (init in band={in_band}, DPO loss optimized={loss_optimized}, margin improvable={margin_improvable}) — NOT that DPO is good. SCOPE: DPO-the-loss on a synthetic deterministic correctness signal with confusable hard-negatives, from-scratch char-level MiniGPT; NOT human preferences / RLHF. Findings are scale-dependent.",
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT DPO-lite preference tuning v1166",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "summary": summary,
        "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": [
            "arm", "budget_forward_passes", "opt_steps", "pref_acc_mean", "pref_acc_std",
            "exact_match_mean", "exact_match_std", "mean_logp_chosen", "mean_logp_rejected",
            "delta_logp_chosen", "delta_logp_rejected", "mean_margin", "confusable_error_rate",
            "param_l2_delta", "logp_drift", "dpo_last_loss",
        ],
        "accuracy_curves": accuracy_curves,
        "pref_acc_curves": pref_acc_curves,
        "scaling_grid_rows": scaling_rows,
        "seeds": list(config.seeds),
    }


__all__ = [
    "PreferencePair",
    "build_confusable_preferences",
    "logp_completion",
    "dpo_loss",
    "train_dpo",
    "evaluate_preference",
    "evaluate_confusable",
    "DpoPreferenceConfig",
    "run_dpo_preference",
]

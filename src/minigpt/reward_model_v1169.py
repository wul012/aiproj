"""v1169: reward modeling (the RLHF component DPO skips) + best-of-N reranking.

DPO (v1166/v1168) is reward-model-FREE. This version builds the classic RLHF
reward model: a MiniGPT backbone + a scalar head, pooled at the last real token,
trained with the Bradley-Terry pairwise loss

    L = -E[ log σ( r(chosen) - r(rejected) ) ]

on the v1166 confusable preference pairs (chosen = correct op output, rejected =
a different op's output on the same input). Three honest measurements:

1. IN-DISTRIBUTION ranking accuracy — does ``r(chosen) > r(rejected)`` on
   held-out (unseen-input) pairs of the SAME confusable kind it trained on?
2. OFF-DISTRIBUTION generalization — does it still rank chosen above a RANDOM
   corruption? If in-distribution is high but OOD is ~chance, the RM learned the
   narrow training-reject boundary, NOT "correctness" — a shortcut.
3. BEST-OF-N reranking (the applied payoff) — sample N completions from a weak
   base, rerank by the RM, and compare to a random pick of N and to an ORACLE
   (any-of-N correct). If the RM is brittle off-distribution, reranking the
   policy's OWN samples (which are off the RM's training distribution) can
   *degrade* exact-match below a random pick — a concrete demonstration of the
   distributional brittleness behind RLHF reward hacking / over-optimization.

GATE (mirrors the project discipline): the RM must be LEARNABLE in-distribution
(held-out ranking significantly above chance) or the run is ``review``.
``status=="pass"`` certifies the comparison was VALID — never that the RM is good
(the probe makes the unflattering "brittle off-distribution" outcome likely).
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

from minigpt.experiment_utils import build_minigpt, mean_std, significant
from minigpt.model import MiniGPT
from minigpt.report_utils import utc_now
from minigpt.sft_instruction_v1164 import evaluate_instructions
from minigpt.sft_training import train_sft


class RewardModel(nn.Module):
    """MiniGPT backbone + scalar reward head, pooled at the last real token."""

    def __init__(self, vocab_size: int, config) -> None:
        super().__init__()
        self.backbone: MiniGPT = build_minigpt(vocab_size, config)
        self.head = nn.Linear(config.n_embd, 1, bias=False)

    def reward(self, idx: torch.Tensor, last_idx: torch.Tensor) -> torch.Tensor:
        feats = self.backbone.features(idx)                       # (B, T, n_embd)
        pooled = feats[torch.arange(feats.size(0), device=idx.device), last_idx]
        return self.head(pooled).squeeze(-1)                      # (B,)


def _pack(seqs: list[list[int]], pad_id: int, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    n = len(seqs)
    width = max(len(s) for s in seqs)
    X = torch.full((n, width), pad_id, dtype=torch.long)
    last = torch.zeros(n, dtype=torch.long)
    for i, s in enumerate(seqs):
        X[i, : len(s)] = torch.tensor(s, dtype=torch.long)
        last[i] = len(s) - 1
    return X.to(device), last.to(device)


def train_reward_model(
    rm: RewardModel,
    pairs: list[tuple[list[int], list[int]]],
    *,
    steps: int,
    lr: float,
    batch_size: int,
    pad_id: int,
    device: torch.device,
) -> float:
    """Bradley-Terry training. ``pairs`` is ``(chosen_full_ids, rejected_full_ids)``."""
    n = len(pairs)
    if n == 0:
        raise ValueError("no preference pairs to train the reward model on")
    chosen = [c for c, _ in pairs]
    rejected = [r for _, r in pairs]
    optimizer = torch.optim.AdamW(rm.parameters(), lr=lr)
    rm.train()
    last = float("nan")
    for _ in range(steps):
        sel = torch.randint(0, n, (batch_size,), device=device).tolist()
        Xc, lc = _pack([chosen[i] for i in sel], pad_id, device)
        Xr, lr_ = _pack([rejected[i] for i in sel], pad_id, device)
        loss = -F.logsigmoid(rm.reward(Xc, lc) - rm.reward(Xr, lr_)).mean()
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        last = float(loss.item())
    return last


@torch.no_grad()
def rank_accuracy(rm: RewardModel, pairs: list[tuple[list[int], list[int]]], pad_id: int, *, device: torch.device) -> float:
    if not pairs:
        return float("nan")
    rm.eval()
    Xc, lc = _pack([c for c, _ in pairs], pad_id, device)
    Xr, lr_ = _pack([r for _, r in pairs], pad_id, device)
    return float((rm.reward(Xc, lc) > rm.reward(Xr, lr_)).float().mean().item())


@torch.no_grad()
def best_of_n_sweep(
    base: MiniGPT,
    rm: RewardModel,
    prompts: list[tuple[list[int], list[int], str]],
    *,
    n_values: tuple[int, ...],
    eos_id: int,
    max_new_tokens: int,
    pad_id: int,
    block_size: int,
    device: torch.device,
    temperature: float,
) -> dict[int, dict[str, float]]:
    """For each N: generate ``max(n_values)`` samples per prompt ONCE, then for
    each N compute (rerank_em via RM argmax over the first N, random_em = expected
    single-sample accuracy over the N, oracle_em = any-of-N correct)."""
    base.eval()
    rm.eval()
    max_n = max(n_values)
    # correctness flags + full sequences per prompt
    per_prompt_correct: list[list[int]] = []
    per_prompt_seqs: list[list[list[int]]] = []
    for prompt_ids, expected_ids, _op in prompts:
        idx = torch.tensor([prompt_ids], dtype=torch.long, device=device).repeat(max_n, 1)
        out = base.generate(idx, max_new_tokens=max_new_tokens, temperature=temperature, top_k=None)
        flags: list[int] = []
        seqs: list[list[int]] = []
        for row in out.tolist():
            comp = row[len(prompt_ids):]
            if eos_id in comp:
                comp = comp[: comp.index(eos_id) + 1]
            full = (prompt_ids + comp)[:block_size]
            out_no_eos = comp[:-1] if comp and comp[-1] == eos_id else comp
            flags.append(int(out_no_eos == list(expected_ids)))
            seqs.append(full)
        per_prompt_correct.append(flags)
        per_prompt_seqs.append(seqs)

    results: dict[int, dict[str, float]] = {}
    for n in n_values:
        rerank_hits = 0
        random_sum = 0.0
        oracle_hits = 0
        for flags, seqs in zip(per_prompt_correct, per_prompt_seqs):
            f = flags[:n]
            s = seqs[:n]
            X, last = _pack(s, pad_id, device)
            r = rm.reward(X, last)
            best = int(torch.argmax(r).item())
            rerank_hits += f[best]
            random_sum += sum(f) / len(f)
            oracle_hits += int(any(f))
        m = len(prompts)
        results[n] = {
            "rerank_em": rerank_hits / m,
            "random_em": random_sum / m,
            "oracle_em": oracle_hits / m,
        }
    return results


@dataclass
class RewardModelConfig:
    block_size: int = 16
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    rm_steps: int = 600
    rm_lr: float = 1e-3
    base_steps: int = 400            # weak base generator for best-of-N (leave headroom)
    base_lr: float = 3e-3
    n_values: tuple[int, ...] = (1, 4, 8, 16)
    temperature: float = 1.0
    batch_size: int = 32
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 128
    use_rope: bool = True
    max_new_tokens: int = 8
    learnability_margin: float = 0.0   # in-dist ranking must exceed 0.5 by more than its std


REVIEW_VERDICTS = {"reward_model_not_learnable"}
PRIMARY_VERDICTS = {
    "reward_model_generalizes_and_best_of_n_helps",
    "reward_model_brittle_off_distribution_best_of_n_degrades",
    "reward_model_learns_in_distribution_but_fails_off_distribution",
    "reward_model_generalizes_but_best_of_n_still_degrades",
    "reward_model_learns_best_of_n_no_clear_gain",
}


def run_reward_model(
    *,
    vocab_size: int,
    rm_train_pairs: list[tuple[list[int], list[int]]],
    rm_eval_pairs: list[tuple[list[int], list[int]]],
    rm_ood_pairs: list[tuple[list[int], list[int]]],
    base_train: list[tuple[list[int], int]],
    heldout_instructions: list[tuple[list[int], list[int], str]],
    ops: tuple[str, ...],
    pad_id: int,
    eos_id: int,
    config: RewardModelConfig,
    device: torch.device,
    corpus_stats: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    n_values = tuple(sorted(set(config.n_values)))
    max_n = max(n_values)

    indist: list[float] = []
    ood: list[float] = []
    greedy_em: list[float] = []
    bon: dict[int, dict[str, list[float]]] = {n: {"rerank_em": [], "random_em": [], "oracle_em": []} for n in n_values}

    for seed in config.seeds:
        torch.manual_seed(seed)
        rm = RewardModel(vocab_size, config).to(device)
        train_reward_model(rm, rm_train_pairs, steps=config.rm_steps, lr=config.rm_lr,
                           batch_size=config.batch_size, pad_id=pad_id, device=device)
        indist.append(rank_accuracy(rm, rm_eval_pairs, pad_id, device=device))
        ood.append(rank_accuracy(rm, rm_ood_pairs, pad_id, device=device))

        torch.manual_seed(seed * 7 + 1)
        base = build_minigpt(vocab_size, config).to(device)
        train_sft(base, base_train, steps=config.base_steps, lr=config.base_lr,
                  batch_size=config.batch_size, block_size=config.block_size, device=device,
                  pad_id=pad_id, mask_prompt=True)
        greedy_em.append(evaluate_instructions(base, heldout_instructions, eos_id=eos_id,
                                                max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"])
        torch.manual_seed(40_000 + seed)
        sweep = best_of_n_sweep(base, rm, heldout_instructions, n_values=n_values, eos_id=eos_id,
                                max_new_tokens=config.max_new_tokens, pad_id=pad_id, block_size=config.block_size,
                                device=device, temperature=config.temperature)
        for n in n_values:
            for k in ("rerank_em", "random_em", "oracle_em"):
                bon[n][k].append(sweep[n][k])

    indist_mean, indist_std = mean_std(indist)
    ood_mean, ood_std = mean_std(ood)
    greedy_mean, _ = mean_std(greedy_em)

    rows = []
    bon_curves: dict[str, dict[str, float]] = {"rerank_em": {}, "random_em": {}, "oracle_em": {}}
    for n in n_values:
        rr_m, rr_s = mean_std(bon[n]["rerank_em"])
        rnd_m, _ = mean_std(bon[n]["random_em"])
        orc_m, _ = mean_std(bon[n]["oracle_em"])
        bon_curves["rerank_em"][str(n)] = round(rr_m, 6)
        bon_curves["random_em"][str(n)] = round(rnd_m, 6)
        bon_curves["oracle_em"][str(n)] = round(orc_m, 6)
        rows.append({"n": n, "rerank_em_mean": round(rr_m, 6), "rerank_em_std": round(rr_s, 6),
                     "random_em_mean": round(rnd_m, 6), "oracle_em_mean": round(orc_m, 6)})

    # ---- gate: RM learnable in-distribution (ranking significantly above chance) ----
    rm_learnable = significant(indist_mean, indist_std, 0.5 + config.learnability_margin, 0.0)
    if not rm_learnable:
        status, decision, verdict = "review", "reward_model_not_learnable", "reward_model_not_learnable"
    else:
        status, decision, verdict = "pass", "reward_model_measured", "pending"

    generalizes_ood = significant(ood_mean, ood_std, 0.5, 0.0)
    max_rr_m, max_rr_s = mean_std(bon[max_n]["rerank_em"])
    max_rnd_m, max_rnd_s = mean_std(bon[max_n]["random_em"])
    max_orc_m, _ = mean_std(bon[max_n]["oracle_em"])
    bon_helps = significant(max_rr_m, max_rr_s, max_rnd_m, max_rnd_s)
    bon_degrades = significant(max_rnd_m, max_rnd_s, max_rr_m, max_rr_s)

    rm_verdict = "reward_model_generalizes_to_off_distribution" if generalizes_ood else "reward_model_in_distribution_only"
    if bon_helps:
        bon_verdict = "best_of_n_reranking_helps"
    elif bon_degrades:
        bon_verdict = "best_of_n_reranking_degrades"
    else:
        bon_verdict = "best_of_n_reranking_neutral"

    if status == "pass":
        if generalizes_ood and bon_helps:
            verdict = "reward_model_generalizes_and_best_of_n_helps"
        elif (not generalizes_ood) and bon_degrades:
            verdict = "reward_model_brittle_off_distribution_best_of_n_degrades"
        elif not generalizes_ood:
            verdict = "reward_model_learns_in_distribution_but_fails_off_distribution"
        elif bon_degrades:
            verdict = "reward_model_generalizes_but_best_of_n_still_degrades"
        else:
            verdict = "reward_model_learns_best_of_n_no_clear_gain"

    stats = corpus_stats or {}
    summary = {
        "status": status,
        "decision": decision,
        "verdict": verdict,
        "rm_verdict": rm_verdict,
        "best_of_n_verdict": bon_verdict,
        "device": str(device),
        "seeds": len(config.seeds),
        "ops": ",".join(ops),
        "rm_steps": config.rm_steps,
        "base_steps": config.base_steps,
        "n_values": ",".join(str(n) for n in n_values),
        "temperature": config.temperature,
        "n_layer": config.n_layer,
        "n_head": config.n_head,
        "n_embd": config.n_embd,
        "use_rope": config.use_rope,
        "rm_train_pairs": stats.get("rm_train_pairs"),
        "rm_eval_pairs": stats.get("rm_eval_pairs"),
        "rm_ood_pairs": stats.get("rm_ood_pairs"),
        "learnability_margin": config.learnability_margin,
        "rm_indistribution_rank_acc": round(indist_mean, 6),
        "rm_indistribution_rank_acc_std": round(indist_std, 6),
        "rm_ood_rank_acc": round(ood_mean, 6),
        "rm_ood_rank_acc_std": round(ood_std, 6),
        "rm_learnable": rm_learnable,
        "generalizes_off_distribution": generalizes_ood,
        "task_learned": rm_learnable,
        "base_greedy_exact_match": round(greedy_mean, 6),
        "max_n": max_n,
        "best_of_n_rerank_at_max": round(max_rr_m, 6),
        "best_of_n_random_at_max": round(max_rnd_m, 6),
        "best_of_n_oracle_at_max": round(max_orc_m, 6),
        "best_of_n_helps": bon_helps,
        "best_of_n_degrades": bon_degrades,
    }

    recommendations = [
        f"VERDICT ({verdict}): the reward model ranks held-out IN-DISTRIBUTION pairs (chosen vs confusable-reject) at {indist_mean:.3f} but OFF-DISTRIBUTION (chosen vs random corruption) at {ood_mean:.3f} (chance=0.5; generalizes_off_distribution={generalizes_ood}). {len(config.seeds)} seeds, gap-minus-combined-std significance.",
        f"REWARD MODEL ({rm_verdict}): Bradley-Terry loss -logσ(r(chosen)-r(rejected)) on a MiniGPT backbone + scalar head. High in-distribution ranking with chance-level OOD ranking means the RM learned the narrow training-reject boundary, NOT general correctness — a shortcut.",
        f"BEST-OF-N ({bon_verdict}): reranking a weak base's own samples (greedy exact-match {greedy_mean:.3f}) by the RM gives exact-match {max_rr_m:.3f} at N={max_n} vs a random pick {max_rnd_m:.3f} and an oracle (any-of-N correct) {max_orc_m:.3f}. If rerank < random, the brittle RM is actively harmful on the policy's OWN (off-distribution) samples — the distributional brittleness behind reward hacking / over-optimization.",
        "SCOPE: classic RLHF reward modeling on a synthetic deterministic correctness signal with confusable hard-negatives, from-scratch char-level MiniGPT; NOT human preferences / RLHF-at-scale. The oracle column separates 'RM is a bad ranker' from 'the base's samples lack any correct answer'.",
        f"GATE: status='{status}' means the RM was LEARNABLE in-distribution (rank acc {indist_mean:.3f} > 0.5; rm_learnable={rm_learnable}) so the comparison is valid — NOT that the RM is good. The honest finding is whichever data-driven verdict the numbers select.",
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT reward modeling + best-of-N v1169",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "summary": summary,
        "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": ["n", "rerank_em_mean", "rerank_em_std", "random_em_mean", "oracle_em_mean"],
        "best_of_n_curves": bon_curves,
        "seeds": list(config.seeds),
    }


__all__ = [
    "RewardModel",
    "train_reward_model",
    "rank_accuracy",
    "best_of_n_sweep",
    "RewardModelConfig",
    "run_reward_model",
    "REVIEW_VERDICTS",
    "PRIMARY_VERDICTS",
]

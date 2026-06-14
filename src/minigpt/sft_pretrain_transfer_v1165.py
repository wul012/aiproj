"""v1165: the real two-stage SFT recipe — does pretraining transfer to a new task?

v1164 trained instruction-following from scratch and flagged that real SFT
fine-tunes a *pretrained base*. v1165 closes that gap and measures the reason the
two-stage recipe exists: a base LM is pretrained (full next-token loss) on ops
{copy, reverse, sort}, then supervised-fine-tuned (completion-only loss) on a
HELD-OUT new op the base never saw — shift-left (``abcd -> bcda``), a positional
op that shares "attend to a position and copy" primitives with copy/reverse.

Two arms are compared at several SFT budgets:

* ``pretrained`` — load the pretrained base, then SFT on the new op;
* ``scratch`` — random init, then SFT on the new op (same budget).

The honest expectation (measured, not assumed) is that pretraining helps most in
the low-SFT-data regime — data-efficient transfer — and the arms converge as the
SFT budget grows. A learnability gate guards the reading: if the pretrained arm
never learns the new op even at the largest budget, the run is reported as not
learned rather than as a transfer comparison.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

import torch

from minigpt.lm_training import train_lm
from minigpt.model import GPTConfig, MiniGPT
from minigpt.report_utils import utc_now
from minigpt.sft_instruction_v1164 import evaluate_instructions
from minigpt.sft_training import train_sft


@dataclass
class SftTransferConfig:
    block_size: int = 16
    seeds: tuple[int, ...] = (1337, 1338, 1339)
    base_steps: int = 1200
    base_lr: float = 3e-3
    base_batch_size: int = 64
    sft_schedule: tuple[int, ...] = (50, 150, 400, 1000)
    sft_lr: float = 3e-3
    sft_batch_size: int = 64
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 128
    use_rope: bool = True
    max_new_tokens: int = 8
    learnability_gate: float = 0.5  # pretrained arm at max SFT budget must exceed this


def _build(vocab_size: int, config: SftTransferConfig) -> MiniGPT:
    return MiniGPT(
        GPTConfig(
            vocab_size=vocab_size, block_size=config.block_size, n_layer=config.n_layer,
            n_head=config.n_head, n_embd=config.n_embd, dropout=0.0, use_rope=config.use_rope,
        )
    )


def _mean_std(values: list[float]) -> tuple[float, float]:
    clean = [v for v in values if v is not None]
    if not clean:
        return float("nan"), 0.0
    return sum(clean) / len(clean), (statistics.stdev(clean) if len(clean) > 1 else 0.0)


def run_sft_transfer(
    *,
    vocab_size: int,
    base_train_ids: torch.Tensor,
    downstream_train: list[tuple[list[int], int]],
    downstream_heldout: list[tuple[list[int], list[int], str]],
    downstream_op: str,
    pad_id: int,
    eos_id: int,
    config: SftTransferConfig,
    device: torch.device,
    corpus_stats: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    schedule = tuple(sorted(set(config.sft_schedule)))
    arms = ("pretrained", "scratch")
    # acc[arm][budget] = list over seeds
    acc: dict[str, dict[int, list[float]]] = {a: {b: [] for b in schedule} for a in arms}

    for seed in config.seeds:
        # Pretrain the base once per seed (full next-token LM on {C,R,S}).
        torch.manual_seed(seed)
        base = _build(vocab_size, config).to(device)
        train_lm(base, list(base.parameters()), base_train_ids, steps=config.base_steps,
                 lr=config.base_lr, batch_size=config.base_batch_size, block_size=config.block_size, device=device)
        base_state = {k: v.detach().clone() for k, v in base.state_dict().items()}

        for budget in schedule:
            # Same SFT-batch sampling stream for both arms at this (seed, budget):
            # the ONLY difference is the initial weights (pretrained vs random).
            sft_seed = 10_000 + seed * 13 + budget

            model_p = _build(vocab_size, config).to(device)
            model_p.load_state_dict(base_state)
            torch.manual_seed(sft_seed)
            train_sft(model_p, downstream_train, steps=budget, lr=config.sft_lr,
                      batch_size=config.sft_batch_size, block_size=config.block_size, device=device,
                      pad_id=pad_id, mask_prompt=True)
            acc["pretrained"][budget].append(
                evaluate_instructions(model_p, downstream_heldout, eos_id=eos_id,
                                      max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"]
            )

            torch.manual_seed(seed * 7 + 1)
            model_s = _build(vocab_size, config).to(device)
            torch.manual_seed(sft_seed)
            train_sft(model_s, downstream_train, steps=budget, lr=config.sft_lr,
                      batch_size=config.sft_batch_size, block_size=config.block_size, device=device,
                      pad_id=pad_id, mask_prompt=True)
            acc["scratch"][budget].append(
                evaluate_instructions(model_s, downstream_heldout, eos_id=eos_id,
                                      max_new_tokens=config.max_new_tokens, device=device)["overall_accuracy"]
            )

    rows = []
    curves: dict[str, dict[str, float]] = {a: {} for a in arms}
    for arm in arms:
        for b in schedule:
            m, s = _mean_std(acc[arm][b])
            rows.append({"arm": arm, "sft_steps": b, "exact_match_mean": round(m, 6), "exact_match_std": round(s, 6)})
            curves[arm][str(b)] = round(m, 6)

    min_b, max_b = min(schedule), max(schedule)
    pre_max_mean, _ = _mean_std(acc["pretrained"][max_b])
    task_learned = pre_max_mean >= config.learnability_gate

    def _gap(b: int) -> tuple[float, float]:
        pm, ps = _mean_std(acc["pretrained"][b])
        sm, ss = _mean_std(acc["scratch"][b])
        return pm - sm, (ps ** 2 + ss ** 2) ** 0.5

    gap_lo, cstd_lo = _gap(min_b)
    gap_hi, cstd_hi = _gap(max_b)
    sig_lo, sig_hi = gap_lo - cstd_lo > 0, gap_hi - cstd_hi > 0

    if not task_learned:
        status, decision, verdict = "review", "downstream_op_not_learned", "downstream_op_not_learned"
    else:
        status, decision = "pass", "sft_transfer_measured"
        if sig_lo and not sig_hi:
            verdict = "pretraining_transfers_most_in_low_data_regime"
        elif sig_lo and sig_hi:
            verdict = "pretraining_improves_downstream_sft"
        elif not sig_lo and sig_hi:
            verdict = "pretraining_benefit_emerges_with_more_sft"
        else:
            verdict = "no_measurable_transfer_at_this_scale"

    pre_min_mean, _ = _mean_std(acc["pretrained"][min_b])
    scr_min_mean, _ = _mean_std(acc["scratch"][min_b])
    scr_max_mean, _ = _mean_std(acc["scratch"][max_b])

    summary = {
        "status": status,
        "decision": decision,
        "verdict": verdict,
        "device": str(device),
        "seeds": len(config.seeds),
        "downstream_op": downstream_op,
        "base_ops": (corpus_stats or {}).get("base_ops"),
        "base_steps": config.base_steps,
        "sft_schedule": ",".join(str(b) for b in schedule),
        "n_layer": config.n_layer,
        "n_head": config.n_head,
        "n_embd": config.n_embd,
        "use_rope": config.use_rope,
        "base_train_char_count": (corpus_stats or {}).get("base_train_char_count"),
        "downstream_train_count": (corpus_stats or {}).get("downstream_train_count"),
        "downstream_heldout_count": (corpus_stats or {}).get("downstream_heldout_count"),
        "learnability_gate": config.learnability_gate,
        "pretrained_at_max_budget": round(pre_max_mean, 6),
        "task_learned": task_learned,
        "min_sft_steps": min_b,
        "max_sft_steps": max_b,
        "pretrained_at_min": round(pre_min_mean, 6),
        "scratch_at_min": round(scr_min_mean, 6),
        "transfer_gap_at_min": round(gap_lo, 6),
        "scratch_at_max": round(scr_max_mean, 6),
        "transfer_gap_at_max": round(gap_hi, 6),
    }

    recommendations = [
        f"VERDICT ({verdict}): on the held-out op '{downstream_op}', pretrained-vs-scratch SFT exact-match gap is {gap_lo:+.3f} at {min_b} SFT steps and {gap_hi:+.3f} at {max_b} SFT steps ({len(config.seeds)} seeds). Pretraining on {{copy,reverse,sort}} is expected to help most when downstream SFT data/compute is small.",
        f"DATA EFFICIENCY: at {min_b} SFT steps the pretrained base reaches {pre_min_mean:.3f} exact-match on the new op vs {scr_min_mean:.3f} from scratch; by {max_b} steps they are {pre_max_mean:.3f} vs {scr_max_mean:.3f}. The new op (shift-left) was NEVER in base pretraining, so any gap is transfer of shared primitives + the instruction format, not leakage.",
        f"Learnability gate: the pretrained arm reaches {pre_max_mean:.3f} exact-match on the new op at {max_b} steps (gate {config.learnability_gate}); task_learned={task_learned}.",
        "RECIPE: this is the real two-stage SFT pipeline — pretrain a base with full next-token loss, then fine-tune with completion-only loss on a downstream task. The base and downstream share one char vocabulary so embeddings transfer.",
        "SCOPE: tiny from-scratch base and a synthetic op family; transfer magnitude is scale-dependent and the new op deliberately shares positional-copy primitives with the pretrained ops, so this shows the MECHANISM of transfer, not a generic claim.",
    ]

    return {
        "schema_version": 1,
        "title": "MiniGPT base->SFT transfer to a held-out op v1165",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "summary": summary,
        "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": ["arm", "sft_steps", "exact_match_mean", "exact_match_std"],
        "accuracy_curves": curves,
        "seeds": list(config.seeds),
    }


__all__ = ["SftTransferConfig", "run_sft_transfer"]

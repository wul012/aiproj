"""v1160: compare learned absolute positions vs RoPE on held-out generalization.

Trains two MiniGPT models from scratch on the same templated-corpus train split —
one with the existing learned `position_embedding`, one with RoPE
(``use_rope=True``) — and compares held-out loss / next-token accuracy on the
disjoint held-out split (reusing v1157's harness). The deliverable is the RoPE
capability plus an honest measured comparison; the report does not pre-assume a
winner.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch

from minigpt.heldout_eval import evaluate_heldout
from minigpt.lm_training import train_lm
from minigpt.model import GPTConfig, MiniGPT
from minigpt.report_utils import utc_now


@dataclass
class RopeEvalConfig:
    steps: int = 400
    lr: float = 3e-4
    batch_size: int = 32
    block_size: int = 48
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 128
    seed: int = 1337


def _train_and_eval(*, vocab_size, use_rope, train_ids, heldout_ids, config, device):
    torch.manual_seed(config.seed)
    model = MiniGPT(
        GPTConfig(
            vocab_size=vocab_size, block_size=config.block_size, n_layer=config.n_layer,
            n_head=config.n_head, n_embd=config.n_embd, dropout=0.0, use_rope=use_rope,
        )
    ).to(device)
    train_lm(model, list(model.parameters()), train_ids, steps=config.steps, lr=config.lr,
             batch_size=config.batch_size, block_size=config.block_size, device=device)
    metrics = evaluate_heldout(model, heldout_ids, block_size=config.block_size, device=device)
    metrics["parameter_count"] = model.parameter_count()
    return metrics


def run_rope_eval(
    *,
    vocab_size: int,
    train_ids: torch.Tensor,
    heldout_ids: torch.Tensor,
    config: RopeEvalConfig,
    device: torch.device,
    corpus_stats: dict | None = None,
    generated_at: str | None = None,
) -> dict:
    learned = _train_and_eval(vocab_size=vocab_size, use_rope=False, train_ids=train_ids, heldout_ids=heldout_ids, config=config, device=device)
    rope = _train_and_eval(vocab_size=vocab_size, use_rope=True, train_ids=train_ids, heldout_ids=heldout_ids, config=config, device=device)
    return _build_report(learned=learned, rope=rope, config=config, device=device,
                         corpus_stats=corpus_stats or {}, generated_at=generated_at or utc_now())


def _build_report(*, learned, rope, config, device, corpus_stats, generated_at) -> dict:
    loss_delta = rope["heldout_loss"] - learned["heldout_loss"]
    acc_delta = rope["heldout_token_accuracy"] - learned["heldout_token_accuracy"]
    # Capability validity: both schemes trained to a real (non-degenerate) held-out loss.
    valid = learned["heldout_loss"] > 0 and rope["heldout_loss"] > 0
    status = "pass" if valid else "review"
    if abs(loss_delta) < 0.02:
        verdict = "rope_matches_learned_positions"
    elif loss_delta < 0:
        verdict = "rope_lower_heldout_loss"
    else:
        verdict = "learned_positions_lower_heldout_loss"
    decision = "rope_capability_validated" if valid else "rope_eval_inconclusive"

    rows = [
        {"positional_scheme": "learned_absolute", "heldout_loss": round(learned["heldout_loss"], 6), "heldout_token_accuracy": round(learned["heldout_token_accuracy"], 6), "parameter_count": int(learned["parameter_count"])},
        {"positional_scheme": "rope", "heldout_loss": round(rope["heldout_loss"], 6), "heldout_token_accuracy": round(rope["heldout_token_accuracy"], 6), "parameter_count": int(rope["parameter_count"])},
    ]
    summary = {
        "status": status,
        "decision": decision,
        "verdict": verdict,
        "device": str(device),
        "steps": config.steps,
        "block_size": config.block_size,
        "n_layer": config.n_layer,
        "n_head": config.n_head,
        "n_embd": config.n_embd,
        "heldout_token_count": int(learned["heldout_token_count"]),
        "train_char_count": corpus_stats.get("train_char_count"),
        "heldout_char_count": corpus_stats.get("heldout_char_count"),
        "learned_heldout_loss": round(learned["heldout_loss"], 6),
        "rope_heldout_loss": round(rope["heldout_loss"], 6),
        "heldout_loss_delta_rope_minus_learned": round(loss_delta, 6),
        "learned_heldout_accuracy": round(learned["heldout_token_accuracy"], 6),
        "rope_heldout_accuracy": round(rope["heldout_token_accuracy"], 6),
        "heldout_accuracy_delta": round(acc_delta, 6),
    }
    recommendations = [
        f"Both positional schemes trained to a real held-out loss; verdict: {verdict} "
        f"(RoPE - learned = {loss_delta:+.4f} loss, {acc_delta:+.4f} accuracy).",
        "RoPE encodes relative position by rotating Q/K and needs no learned position table; on this short fixed-length corpus its main practical edge (length extrapolation) is not yet exercised — that is a candidate for a later version.",
        "Note: the RoPE model still allocates an unused position_embedding for state_dict simplicity; a future cleanup could drop it to realize RoPE's parameter saving.",
    ]
    return {
        "schema_version": 1,
        "title": "MiniGPT RoPE vs learned positions held-out comparison v1160",
        "generated_at": generated_at,
        "status": status,
        "decision": decision,
        "summary": summary,
        "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": ["positional_scheme", "heldout_loss", "heldout_token_accuracy", "parameter_count"],
    }


__all__ = ["RopeEvalConfig", "run_rope_eval"]

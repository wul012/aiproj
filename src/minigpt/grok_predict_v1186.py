"""v1186: use the canonical grokking checkpoint — a tiny inference API + demo.

v1185 trained and saved a self-contained grokking checkpoint. v1186 closes the
productize loop: a minimal API to LOAD that checkpoint and compute `a + b (mod p)`
with it, plus a demo that re-derives the held-out accuracy directly from the
shipped `.pt` (independent of the v1185 training run) and decodes the learned
modular-addition table.

Inference detail: the model was trained on `[a, +, b, =, c]` with loss at the
`=` position predicting `c`. To USE it we feed only the 4-token prompt
`[a, +, b, =]` and read the next-token logits at the last position — standard
autoregressive decoding. No training, no GPU required.
"""

from __future__ import annotations

from pathlib import Path

import torch

from minigpt.grok_checkpoint_v1185 import CheckpointMeta, load_checkpoint
from minigpt.grok_v1179 import ANSWER_TARGET_POS, build_modular_task, split_indices
from minigpt.model import MiniGPT
from minigpt.report_utils import utc_now

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHECKPOINT = ROOT / "f" / "1185" / "解释" / "grok_checkpoint_v1185" / "grok_checkpoint_v1185.pt"


def encode_problem(a: int, b: int, p: int, device: torch.device | None = None) -> torch.Tensor:
    """The 4-token prompt ``[a, PLUS, b, EQ]`` (the answer is what we predict)."""
    return torch.tensor([[a, p, b, p + 1]], dtype=torch.long, device=device)


@torch.no_grad()
def predict(model: MiniGPT, a: int, b: int, p: int) -> int:
    """Predict ``(a + b) mod p`` by reading the next-token logits after ``=``."""
    model.eval()
    device = next(model.parameters()).device
    logits, _ = model(encode_problem(a, b, p, device))
    return int(logits[:, -1, :].argmax(dim=-1).item())


@torch.no_grad()
def predict_pairs(model: MiniGPT, pairs: list[tuple[int, int]], p: int) -> list[dict]:
    """Decode a list of (a, b) problems into prediction/truth/correct rows."""
    rows = []
    for a, b in pairs:
        pred = predict(model, a, b, p)
        truth = (a + b) % p
        rows.append({"a": a, "b": b, "predicted": pred, "truth": truth, "correct": pred == truth})
    return rows


@torch.no_grad()
def evaluate_table(model: MiniGPT, meta: CheckpointMeta) -> dict:
    """Predict every (a, b) pair with the loaded model and split the accuracy into
    train vs held-out using the checkpoint's own seed/train_frac — an independent
    re-derivation of the shipped checkpoint's generalization."""
    p = meta.p
    data = build_modular_task(p)
    device = next(model.parameters()).device
    model.eval()
    logits, _ = model(data[:, :4].to(device))  # 4-token prompts for all pairs
    pred = logits[:, -1, :].argmax(dim=-1).cpu()
    truth = data[:, ANSWER_TARGET_POS]
    correct = pred == truth

    train_idx, val_idx = split_indices(data.shape[0], meta.train_frac, meta.seed)
    train_acc = correct.index_select(0, train_idx).float().mean().item()
    heldout_acc = correct.index_select(0, val_idx).float().mean().item()
    return {
        "p": p,
        "overall_acc": round(correct.float().mean().item(), 6),
        "train_acc": round(train_acc, 6),
        "heldout_acc": round(heldout_acc, 6),
        "n_total": int(correct.numel()),
        "n_heldout": int(val_idx.numel()),
        "n_heldout_correct": int(correct.index_select(0, val_idx).sum().item()),
        "pred": pred,  # tensors for the figure; dropped before serialization
        "truth": truth,
    }


# A few well-known pairs for the human-readable demo (both small and large operands).
DEMO_PAIRS = [(36, 37), (4, 1), (50, 50), (96, 96), (0, 0), (40, 80)]


def build_report(meta: CheckpointMeta, table: dict, demo_rows: list[dict], checkpoint_path: str,
                 generated_at: str | None = None) -> dict:
    """Readability report: which checkpoint, the re-derived train/held-out
    accuracy, and the decoded demo problems."""
    usable = table["heldout_acc"] >= 0.90 and table["train_acc"] >= 0.99
    demo_all_correct = all(r["correct"] for r in demo_rows)
    if not usable:
        verdict = "checkpoint_loaded_but_weak"
    elif not demo_all_correct:
        verdict = "checkpoint_usable_but_demo_pair_wrong"
    else:
        verdict = "grokking_checkpoint_usable"
    status = "pass" if verdict == "grokking_checkpoint_usable" else "review"

    summary = {
        "checkpoint": checkpoint_path,
        "p": meta.p,
        "recipe_weight_decay": meta.weight_decay,
        "train_frac": meta.train_frac,
        "seed": meta.seed,
        "overall_acc": table["overall_acc"],
        "train_acc": table["train_acc"],
        "heldout_acc": table["heldout_acc"],
        "n_heldout": table["n_heldout"],
        "demo_pairs": len(demo_rows),
        "demo_all_correct": demo_all_correct,
        "verdict": verdict,
        "usage": "load_checkpoint(path) -> model; predict(model, a, b, p) -> (a+b) mod p",
        "boundary": "toy_scale_single_task_inference_demo_not_a_scaling_claim",
    }
    return {
        "schema_version": 1,
        "title": "MiniGPT v1186 grokking checkpoint inference demo",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": verdict,
        "summary": summary,
        "rows": demo_rows,
        "recommendations": _recommendations(verdict, table),
        "csv_fieldnames": ["a", "b", "predicted", "truth", "correct"],
    }


def _recommendations(verdict: str, table: dict) -> list[str]:
    if verdict == "grokking_checkpoint_usable":
        return [
            f"The shipped checkpoint loads and computes a+b mod {table['p']}: held-out accuracy {table['heldout_acc']:.3f} on {table['n_heldout']} unseen pairs, re-derived independently of the v1185 training run.",
            "Usage: model, meta = load_checkpoint(path); predict(model, a, b, meta.p).",
        ]
    if verdict == "checkpoint_loaded_but_weak":
        return ["The checkpoint loaded but its re-derived held-out/train accuracy is below threshold — it is not the canonical grokked checkpoint."]
    return ["The checkpoint is usable but a known demo pair decoded incorrectly — check the inference prompt encoding."]


def load_default(device: torch.device | None = None) -> tuple[MiniGPT, CheckpointMeta]:
    """Load the committed canonical v1185 checkpoint."""
    return load_checkpoint(DEFAULT_CHECKPOINT, device=device)


__all__ = [
    "DEFAULT_CHECKPOINT", "DEMO_PAIRS", "encode_problem", "predict", "predict_pairs",
    "evaluate_table", "build_report", "load_default",
]

"""v1185: the canonical grokking checkpoint — productize, don't sweep.

v1179 reproduced grokking on `a + b = c (mod 97)`; v1183 swept weight decay and
found an interior optimum (fastest grok at wd=1.0). v1180-v1184 audited those two
experiments. v1185 stops sweeping and *productizes* the result: it freezes the
default grokking recipe (using wd=1.0 because v1183 showed it is the optimum),
trains ONE canonical model to grok, and saves a self-contained checkpoint
(weights + config + vocab scheme + split seed + metrics + curve) plus a small
demo that loads it back and proves "memorize first, then generalize" on held-out
pairs.

This is engineering, not new science: one cheap training run (early-stopped once
grokking is confirmed), a save/load round-trip, and a held-out generalization
demo. status == "pass" IFF the model actually grokked, the held-out accuracy is
high, and the saved checkpoint reloads to identical logits.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch

from minigpt.grok_v1179 import (
    ANSWER_READ_POS,
    ANSWER_TARGET_POS,
    GrokConfig,
    answer_accuracy,
    answer_loss,
    build_modular_task,
    make_grok_model,
    split_indices,
)
from minigpt.model import MiniGPT
from minigpt.report_utils import utc_now
from minigpt.script_runtime import seed_everything

# The frozen default recipe. wd=1.0 is the v1183 interior optimum; train_frac=0.2
# is the v1179-calibrated grokking regime; a single fixed seed makes the shipped
# checkpoint canonical and reproducible.
CANONICAL_CONFIG = GrokConfig(seeds=(1337,), wds=(1.0,))


@dataclass
class CheckpointMeta:
    """Everything needed to rebuild the model and reproduce the split, plus the
    grokking metrics. Stored alongside the weights so the checkpoint is
    self-contained."""

    p: int
    train_frac: float
    seed: int
    weight_decay: float
    vocab_size: int
    n_layer: int
    n_head: int
    n_embd: int
    block_size: int
    t_mem: int | None
    t_gen: int | None
    final_train_acc: float
    final_val_acc: float
    steps_run: int

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def train_to_grok(config: GrokConfig, device: torch.device) -> tuple[MiniGPT, CheckpointMeta, list[dict]]:
    """Train the canonical recipe to grok and return the trained model, metadata,
    and the train/val accuracy curve. Uses the v1179 primitives; full-batch AdamW;
    stops once a stable grok is confirmed, otherwise runs the full budget."""
    seed = config.seeds[0]
    weight_decay = config.wds[0]
    vocab_size = config.p + 2
    full_data = build_modular_task(config.p)

    seed_everything(seed)
    train_idx, val_idx = split_indices(full_data.shape[0], config.train_frac, seed)
    model = make_grok_model(vocab_size, config).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.lr, betas=(config.beta1, config.beta2), weight_decay=weight_decay
    )
    train = full_data.index_select(0, train_idx).to(device)
    val = full_data.index_select(0, val_idx).to(device)

    curve: list[dict] = []
    t_mem: int | None = None
    t_gen: int | None = None
    last_train_acc = 0.0
    last_val_acc = 0.0
    step = 0
    while True:
        if step % config.eval_every == 0 or step == config.max_steps:
            train_acc = answer_accuracy(model, train)
            val_acc = answer_accuracy(model, val)
            curve.append({"step": step, "train_acc": round(train_acc, 6), "val_acc": round(val_acc, 6)})
            last_train_acc, last_val_acc = train_acc, val_acc
            if t_mem is None and train_acc >= config.train_acc_thresh:
                t_mem = step
            if t_gen is None and val_acc >= config.val_acc_thresh:
                t_gen = step
            if t_gen is not None and val_acc >= config.grok_stop_val:
                break
        if step >= config.max_steps:
            break
        model.train()
        optimizer.zero_grad(set_to_none=True)
        answer_loss(model, train).backward()
        optimizer.step()
        step += 1

    meta = CheckpointMeta(
        p=config.p, train_frac=config.train_frac, seed=seed, weight_decay=weight_decay,
        vocab_size=vocab_size, n_layer=config.n_layer, n_head=config.n_head, n_embd=config.n_embd,
        block_size=model.config.block_size, t_mem=t_mem, t_gen=t_gen,
        final_train_acc=round(last_train_acc, 6), final_val_acc=round(last_val_acc, 6),
        steps_run=curve[-1]["step"],
    )
    return model, meta, curve


def save_checkpoint(model: MiniGPT, meta: CheckpointMeta, path: str | Path) -> None:
    """Save weights + meta as one self-contained ``.pt`` file."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "meta": meta.as_dict()}, out)


def load_checkpoint(path: str | Path, device: torch.device | None = None) -> tuple[MiniGPT, CheckpointMeta]:
    """Rebuild the model from a checkpoint and load its weights. Self-contained:
    the meta carries the config needed to reconstruct the architecture."""
    device = device or torch.device("cpu")
    payload = torch.load(Path(path), map_location=device, weights_only=False)
    meta = CheckpointMeta(**payload["meta"])
    config = GrokConfig(
        p=meta.p, train_frac=meta.train_frac, n_layer=meta.n_layer,
        n_head=meta.n_head, n_embd=meta.n_embd, seeds=(meta.seed,), wds=(meta.weight_decay,),
    )
    model = make_grok_model(meta.vocab_size, config).to(device)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, meta


@torch.no_grad()
def evaluate_generalization(model: MiniGPT, meta: CheckpointMeta, device: torch.device, n_samples: int = 8) -> dict:
    """Held-out accuracy + a few decoded (a, b, predicted, truth) demo rows — the
    proof that the checkpoint generalizes to unseen pairs."""
    full_data = build_modular_task(meta.p)
    _, val_idx = split_indices(full_data.shape[0], meta.train_frac, meta.seed)
    val = full_data.index_select(0, val_idx).to(device)
    model.eval()
    logits, _ = model(val)
    pred = logits[:, ANSWER_READ_POS, :].argmax(dim=-1)
    truth = val[:, ANSWER_TARGET_POS]
    heldout_acc = (pred == truth).float().mean().item()

    samples: list[dict] = []
    for i in range(min(n_samples, val.shape[0])):
        a, b = int(val[i, 0]), int(val[i, 2])
        p_i, t_i = int(pred[i]), int(truth[i])
        samples.append({"a": a, "b": b, "predicted": p_i, "truth": t_i, "correct": p_i == t_i})
    return {"heldout_acc": round(heldout_acc, 6), "n_heldout": int(val.shape[0]), "samples": samples}


def logits_match(model_a: MiniGPT, model_b: MiniGPT, p: int, tol: float = 1e-6) -> bool:
    """True iff two models give identical answer-token logits on the full task —
    the save/load round-trip correctness check. Device-safe: each model is fed a
    copy of the task on its own device and the logits are compared on CPU."""
    data = build_modular_task(p)
    model_a.eval()
    model_b.eval()
    with torch.no_grad():
        la, _ = model_a(data.to(next(model_a.parameters()).device))
        lb, _ = model_b(data.to(next(model_b.parameters()).device))
    return torch.allclose(la.cpu(), lb.cpu(), atol=tol)


def build_report(meta: CheckpointMeta, curve: list[dict], demo: dict, roundtrip_ok: bool,
                 generated_at: str | None = None) -> dict:
    """Readability report: the frozen recipe, the grokking metrics, the held-out
    generalization demo, and the memorize-first-then-generalize phase summary."""
    grokked = meta.t_gen is not None
    memorized = meta.t_mem is not None
    delay = (meta.t_gen - meta.t_mem) if (grokked and memorized) else None
    heldout_strong = demo["heldout_acc"] >= 0.90

    if not memorized:
        verdict = "checkpoint_failed_to_memorize"
    elif not grokked:
        verdict = "checkpoint_memorized_but_did_not_grok"
    elif not roundtrip_ok:
        verdict = "checkpoint_grokked_but_roundtrip_mismatch"
    elif not heldout_strong:
        verdict = "checkpoint_grokked_but_weak_heldout"
    else:
        verdict = "canonical_grokking_checkpoint_ready"

    status = "pass" if verdict == "canonical_grokking_checkpoint_ready" else "review"

    rows = [
        {"a": s["a"], "b": s["b"], "predicted": s["predicted"], "truth": s["truth"], "correct": s["correct"]}
        for s in demo["samples"]
    ]
    summary = {
        "recipe": f"a+b mod {meta.p}, 1-layer MiniGPT n_embd={meta.n_embd}, AdamW lr=1e-3 wd={meta.weight_decay}, train_frac={meta.train_frac}",
        "p": meta.p,
        "weight_decay": meta.weight_decay,
        "train_frac": meta.train_frac,
        "seed": meta.seed,
        "vocab_size": meta.vocab_size,
        "memorize_step": meta.t_mem,
        "generalize_step": meta.t_gen,
        "grok_delay_steps": delay,
        "final_train_acc": meta.final_train_acc,
        "final_val_acc": meta.final_val_acc,
        "heldout_acc": demo["heldout_acc"],
        "n_heldout": demo["n_heldout"],
        "roundtrip_logits_identical": roundtrip_ok,
        "verdict": verdict,
        "story": "train accuracy saturates at the memorize step; validation stays near chance until the much-later generalize step (grokking).",
        "boundary": "toy_scale_single_task_modular_addition_canonical_checkpoint_not_a_scaling_claim",
    }
    return {
        "schema_version": 1,
        "title": "MiniGPT v1185 canonical grokking checkpoint",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": verdict,
        "summary": summary,
        "rows": rows,
        "curve": curve,
        "recommendations": _recommendations(verdict, meta, demo),
        "csv_fieldnames": ["a", "b", "predicted", "truth", "correct"],
    }


def _recommendations(verdict: str, meta: CheckpointMeta, demo: dict) -> list[str]:
    if verdict == "canonical_grokking_checkpoint_ready":
        return [
            f"Canonical grokking checkpoint ready: memorized at step {meta.t_mem}, generalized at step {meta.t_gen}, held-out accuracy {demo['heldout_acc']:.3f}.",
            "Load it with load_checkpoint(); it reconstructs the architecture from the embedded meta and reproduces identical logits.",
            "The recipe uses weight_decay=1.0 because the v1183 dose-response found that to be the interior optimum (fastest grok).",
        ]
    if verdict == "checkpoint_memorized_but_did_not_grok":
        return ["The model memorized but did not grok within budget — increase max_steps or recheck the recipe before shipping a checkpoint."]
    if verdict == "checkpoint_grokked_but_roundtrip_mismatch":
        return ["The model grokked but the saved checkpoint did not reload to identical logits — fix the save/load path before shipping."]
    if verdict == "checkpoint_grokked_but_weak_heldout":
        return ["The model grokked but held-out accuracy is below threshold — do not ship as a canonical generalizing checkpoint."]
    return ["The model failed to even memorize the train set — training is broken."]


__all__ = [
    "CANONICAL_CONFIG", "CheckpointMeta", "train_to_grok", "save_checkpoint",
    "load_checkpoint", "evaluate_generalization", "logits_match", "build_report",
]

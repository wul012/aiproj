"""LoRA fine-tuning orchestration for MiniGPT.

This module trains only the LoRA adapter parameters on top of a frozen MiniGPT
model and produces a structured, readable report comparing validation/training
loss *before* and *after* adaptation. The report is the genuine ML evidence: it
shows that a tiny fraction of trainable parameters can still lower the loss.

The orchestration is deliberately decoupled from disk so it can be unit-tested
with in-memory tensors; the v1156 script wires it to a real checkpoint and the
readability artifact writer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import torch
import torch.nn as nn

from minigpt.dataset import get_batch
from minigpt.lora import (
    LoRAConfig,
    apply_lora,
    count_parameters,
    lora_parameters,
    mark_only_lora_as_trainable,
)
from minigpt.report_utils import utc_now


@dataclass
class LoRAFinetuneConfig:
    """Hyper-parameters for a LoRA fine-tuning run."""

    r: int = 8
    alpha: float = 16.0
    dropout: float = 0.0
    target_modules: tuple[str, ...] = ("c_attn", "c_proj")
    target_all_linear: bool = False
    steps: int = 200
    batch_size: int = 16
    learning_rate: float = 1e-3
    eval_iters: int = 20
    eval_interval: int = 50
    seed: int = 1337

    def lora_config(self) -> LoRAConfig:
        return LoRAConfig(
            r=self.r,
            alpha=self.alpha,
            dropout=self.dropout,
            target_modules=self.target_modules,
            target_all_linear=self.target_all_linear,
        )


@torch.no_grad()
def estimate_loss(
    model: nn.Module,
    train_data: torch.Tensor,
    val_data: torch.Tensor,
    *,
    block_size: int,
    batch_size: int,
    eval_iters: int,
    device: torch.device,
) -> dict[str, float]:
    """Average train/val loss over a few random batches (model put in eval mode)."""
    was_training = model.training
    model.eval()
    out: dict[str, float] = {}
    for split, data in (("train", train_data), ("val", val_data)):
        losses = torch.empty(eval_iters)
        for k in range(eval_iters):
            x, y = get_batch(data, block_size, batch_size, device)
            _, loss = model(x, y)
            if loss is None:
                raise RuntimeError("model returned no loss during evaluation")
            losses[k] = loss.item()
        out[split] = float(losses.mean())
    if was_training:
        model.train()
    return out


def run_lora_finetune(
    model: nn.Module,
    train_data: torch.Tensor,
    val_data: torch.Tensor,
    *,
    config: LoRAFinetuneConfig,
    device: torch.device | None = None,
    generated_at: str | None = None,
) -> dict:
    """Fine-tune only LoRA adapters and return a before/after report dict.

    The model is mutated in place: targeted Linear layers become ``LoRALinear``
    and every non-LoRA parameter is frozen.
    """
    device = device or next(model.parameters()).device
    block_size = model.config.block_size
    torch.manual_seed(config.seed)

    base_total = sum(param.numel() for param in model.parameters())

    before = estimate_loss(
        model,
        train_data,
        val_data,
        block_size=block_size,
        batch_size=config.batch_size,
        eval_iters=config.eval_iters,
        device=device,
    )

    replaced = apply_lora(model, config.lora_config())
    mark_only_lora_as_trainable(model)
    model.to(device)
    counts = count_parameters(model)

    trainable = lora_parameters(model)
    optimizer = torch.optim.AdamW(trainable, lr=config.learning_rate)

    history: list[dict[str, float]] = []
    model.train()
    last_loss = float("nan")
    for step in range(1, config.steps + 1):
        x, y = get_batch(train_data, block_size, config.batch_size, device)
        _, loss = model(x, y)
        if loss is None:
            raise RuntimeError("model returned no loss during fine-tuning")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        last_loss = float(loss.item())
        if step == 1 or step % config.eval_interval == 0 or step == config.steps:
            snapshot = estimate_loss(
                model,
                train_data,
                val_data,
                block_size=block_size,
                batch_size=config.batch_size,
                eval_iters=config.eval_iters,
                device=device,
            )
            history.append({"step": step, "train_loss": snapshot["train"], "val_loss": snapshot["val"]})

    after = estimate_loss(
        model,
        train_data,
        val_data,
        block_size=block_size,
        batch_size=config.batch_size,
        eval_iters=config.eval_iters,
        device=device,
    )

    return _build_report(
        replaced=replaced,
        counts=counts,
        before=before,
        after=after,
        history=history,
        last_loss=last_loss,
        config=config,
        device=device,
        base_total=base_total,
        generated_at=generated_at or utc_now(),
    )


def _build_report(
    *,
    replaced: list[str],
    counts: dict[str, float | int],
    before: dict[str, float],
    after: dict[str, float],
    history: list[dict[str, float]],
    last_loss: float,
    config: LoRAFinetuneConfig,
    device: torch.device,
    base_total: int,
    generated_at: str,
) -> dict:
    val_delta = after["val"] - before["val"]
    train_delta = after["train"] - before["train"]
    # Primary, robust signal: did adapter-only training lower the training loss?
    # (Generalization/val loss is only meaningful on a large enough holdout — see caveat.)
    train_improved = after["train"] < before["train"]
    val_improved = after["val"] < before["val"]
    status = "pass" if train_improved else "review"
    decision = "lora_finetune_reduced_train_loss" if train_improved else "lora_finetune_no_train_gain"

    rows = [
        {
            "module": name,
            "kind": "lora_adapter",
            "r": config.r,
            "alpha": config.alpha,
        }
        for name in replaced
    ]

    summary = {
        "status": status,
        "decision": decision,
        "device": str(device),
        "lora_r": config.r,
        "lora_alpha": config.alpha,
        "lora_dropout": config.dropout,
        "target_modules": ", ".join(config.target_modules),
        "adapted_module_count": len(replaced),
        "steps": config.steps,
        "learning_rate": config.learning_rate,
        "base_parameters": int(base_total),
        "trainable_parameters": int(counts["trainable_parameters"]),
        "total_parameters": int(counts["total_parameters"]),
        "trainable_ratio_percent": counts["trainable_ratio_percent"],
        "before_train_loss": round(before["train"], 6),
        "after_train_loss": round(after["train"], 6),
        "train_loss_delta": round(train_delta, 6),
        "before_val_loss": round(before["val"], 6),
        "after_val_loss": round(after["val"], 6),
        "val_loss_delta": round(val_delta, 6),
        "last_step_loss": round(last_loss, 6),
        "train_loss_improved": train_improved,
        "val_loss_improved": val_improved,
    }

    recommendations = []
    if train_improved:
        recommendations.append(
            f"LoRA reduced training loss by {abs(train_delta):.4f} while training only "
            f"{counts['trainable_ratio_percent']}% of parameters; the adapter demonstrably learns."
        )
    else:
        recommendations.append(
            "Training loss did not improve; raise --lora-steps or --lora-lr, or widen --r before treating this adapter as an improvement."
        )
    recommendations.append(
        "Caveat: the bundled corpus is tiny, so validation loss is overfit-dominated and not a reliable "
        "generalization signal. v1157 should introduce a larger real dataset and a held-out eval suite."
    )
    recommendations.append("Merge the adapter with minigpt.lora.merge_lora to serve without extra parameters.")

    return {
        "schema_version": 1,
        "title": "MiniGPT LoRA fine-tune before/after report v1156",
        "generated_at": generated_at,
        "status": status,
        "decision": decision,
        "summary": summary,
        "rows": rows,
        "history": history,
        "recommendations": recommendations,
        "csv_fieldnames": ["module", "kind", "r", "alpha"],
    }


__all__ = [
    "LoRAFinetuneConfig",
    "estimate_loss",
    "run_lora_finetune",
]

"""Model-independent sample plans and teacher-forced window scoring."""

from __future__ import annotations

import random
from dataclasses import dataclass

import torch
from torch.nn import functional as F

from minigpt.core.model import MiniGPT


@dataclass(frozen=True)
class WindowPlan:
    context: int
    starts: tuple[int, ...]
    available: int
    requested: int
    seed: int


def make_plan(token_count: int, context: int, count: int, seed: int) -> WindowPlan:
    if context < 1 or count < 1:
        raise ValueError("context size and window count must be positive")
    available = token_count - context
    if available < 1:
        raise ValueError(f"Evaluation split has {token_count} tokens; context {context} needs at least {context + 1}")
    starts = random.Random(seed).sample(range(available), min(count, available))
    return WindowPlan(context, tuple(starts), available, count, seed)


def select_split(ids: list[int], split: str, ratio: float) -> tuple[torch.Tensor, int]:
    if split == "all":
        return torch.tensor(ids, dtype=torch.long), 0
    if split not in ("train", "val") or not 0 < ratio < 1:
        raise ValueError("Use train/val/all and a train ratio strictly between 0 and 1")
    boundary = max(1, int(len(ids) * ratio))
    offset = boundary if split == "val" else 0
    return torch.tensor(ids[boundary:] if split == "val" else ids[:boundary], dtype=torch.long), offset


def score_windows(
    model: MiniGPT, data: torch.Tensor, plan: WindowPlan, batch_size: int, device: torch.device
) -> list[float]:
    if batch_size < 1 or plan.context > model.config.block_size:
        raise ValueError("Positive batch size and a supported context are required")
    if data.ndim != 1 or len(data) - plan.context != plan.available or not plan.starts:
        raise ValueError("Window plan does not match evaluation data")
    if min(plan.starts) < 0 or max(plan.starts) >= plan.available:
        raise ValueError("Window start is outside evaluation data")
    was_training = model.training
    model.eval()
    losses: list[float] = []
    try:
        with torch.no_grad():
            for begin in range(0, len(plan.starts), batch_size):
                starts = plan.starts[begin : begin + batch_size]
                x = torch.stack([data[s : s + plan.context] for s in starts]).to(device)
                y = torch.stack([data[s + 1 : s + plan.context + 1] for s in starts]).to(device)
                logits, _ = model(x)
                values = F.cross_entropy(logits.transpose(1, 2), y, reduction="none").mean(dim=1)
                if not torch.isfinite(values).all():
                    raise ValueError("Non-finite evaluation loss; no comparison result is valid")
                losses.extend(values.double().cpu().tolist())
    finally:
        model.train(was_training)
    return losses

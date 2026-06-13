"""Shared language-model training loop.

Extracted in v1159 to remove the ``_train`` / ``train_base`` loop that was
copy-pasted across the v1156 runner script and the v1157 / v1158 orchestration
modules. Keeping one implementation means batching, the AdamW step, and the
"train only these params" contract live in exactly one place.

The function trains whatever parameters are passed in ``params`` — pass
``model.parameters()`` for full training, or ``minigpt.lora.lora_parameters(model)``
for adapter-only training. It does not freeze anything itself; freezing is the
caller's job (e.g. via :func:`minigpt.lora.mark_only_lora_as_trainable`).
"""

from __future__ import annotations

from collections.abc import Iterable

import torch
import torch.nn as nn

from minigpt.dataset import get_batch


def train_lm(
    model: nn.Module,
    params: Iterable[nn.Parameter],
    data: torch.Tensor,
    *,
    steps: int,
    lr: float,
    batch_size: int,
    block_size: int,
    device: torch.device,
    log_every: int | None = None,
    label: str = "train",
    weight_decay: float | None = None,
) -> float:
    """Train ``params`` on ``data`` for ``steps`` AdamW steps; return the last batch loss.

    When ``log_every`` is set, prints ``[label] step= loss=`` on the first/last step
    and every ``log_every`` steps (used by the v1156 CLI for progress).

    ``weight_decay`` defaults to ``None``, which keeps AdamW's own default (0.01) so
    every pre-existing caller is byte-for-byte unchanged. Pass ``0.0`` to disable
    decay — v1162 needs this so that parameters which never receive a gradient
    (e.g. position rows beyond the trained length) stay *exactly* at their init.
    """
    optimizer = (
        torch.optim.AdamW(params, lr=lr)
        if weight_decay is None
        else torch.optim.AdamW(params, lr=lr, weight_decay=weight_decay)
    )
    model.train()
    last = float("nan")
    for step in range(1, steps + 1):
        x, y = get_batch(data, block_size, batch_size, device)
        _, loss = model(x, y)
        if loss is None:
            raise RuntimeError("model returned no loss during training")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        last = float(loss.item())
        if log_every and (step == 1 or step % log_every == 0 or step == steps):
            print(f"[{label}] step={step:5d} loss={last:.4f}")
    return last


__all__ = ["train_lm"]

"""Held-out generalization metrics for a MiniGPT model.

Evaluates a model on a held-out token stream with non-overlapping windows and
reports two real, interpretable metrics:

* ``heldout_loss`` — mean per-token cross-entropy (lower = better modelling of
  unseen-but-in-distribution sequences).
* ``heldout_token_accuracy`` — next-token top-1 accuracy (fraction of positions
  where ``argmax(logits)`` equals the true next token).

Because the held-out stream is disjoint from training data (see
:mod:`minigpt.templated_corpus`), these numbers measure generalization, not
memorization.
"""

from __future__ import annotations

import torch
import torch.nn as nn


@torch.no_grad()
def evaluate_heldout(
    model: nn.Module,
    token_ids: list[int] | torch.Tensor,
    *,
    block_size: int,
    device: torch.device,
) -> dict[str, float | int]:
    """Compute held-out loss and next-token accuracy over non-overlapping windows."""
    if isinstance(token_ids, torch.Tensor):
        data = token_ids.detach().to("cpu", dtype=torch.long)
    else:
        data = torch.tensor(list(token_ids), dtype=torch.long)
    if data.numel() < 2:
        raise ValueError("held-out stream must contain at least 2 tokens")

    was_training = model.training
    model.eval()

    total_loss = 0.0
    total_correct = 0
    total_tokens = 0
    window_count = 0
    for start in range(0, data.numel() - 1, block_size):
        chunk = data[start : start + block_size + 1]
        if chunk.numel() < 2:
            break
        x = chunk[:-1].unsqueeze(0).to(device)
        y = chunk[1:].unsqueeze(0).to(device)
        logits, loss = model(x, y)
        if loss is None:
            raise RuntimeError("model returned no loss during held-out evaluation")
        n = y.numel()
        total_loss += float(loss.item()) * n
        total_correct += int((logits.argmax(dim=-1) == y).sum().item())
        total_tokens += n
        window_count += 1

    if was_training:
        model.train()

    return {
        "heldout_loss": total_loss / total_tokens,
        "heldout_token_accuracy": total_correct / total_tokens,
        "heldout_token_count": total_tokens,
        "heldout_window_count": window_count,
    }


__all__ = ["evaluate_heldout"]

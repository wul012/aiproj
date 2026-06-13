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
import torch.nn.functional as F


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


@torch.no_grad()
def evaluate_heldout_per_position(
    model: nn.Module,
    token_ids: list[int] | torch.Tensor,
    *,
    window_len: int,
    device: torch.device,
) -> dict[str, object]:
    """Held-out cross-entropy / accuracy broken down by *within-window position*.

    Uses the same non-overlapping windowing as :func:`evaluate_heldout` (stride
    ``window_len``), but instead of a single scalar it returns the mean per-token
    loss at each position index ``0 .. window_len-1`` inside the window. Because
    every window starts at a fresh offset, the within-window position index equals
    the model's absolute position index for that prediction — which is exactly the
    axis v1162 needs to see whether a learned position table degrades the instant
    the index passes the trained length.

    Averaging ``per_position_loss`` weighted by ``per_position_count`` over all
    positions reproduces :func:`evaluate_heldout`'s scalar ``heldout_loss`` on the
    same window length (asserted by the v1162 regression test).
    """
    if window_len < 1:
        raise ValueError("window_len must be >= 1")
    if isinstance(token_ids, torch.Tensor):
        data = token_ids.detach().to("cpu", dtype=torch.long)
    else:
        data = torch.tensor(list(token_ids), dtype=torch.long)
    if data.numel() < 2:
        raise ValueError("held-out stream must contain at least 2 tokens")

    was_training = model.training
    model.eval()

    pos_loss_sum = [0.0] * window_len
    pos_count = [0] * window_len
    pos_correct = [0] * window_len
    window_count = 0
    for start in range(0, data.numel() - 1, window_len):
        chunk = data[start : start + window_len + 1]
        if chunk.numel() < 2:
            break
        x = chunk[:-1].unsqueeze(0).to(device)
        y = chunk[1:].unsqueeze(0).to(device)
        logits, _ = model(x)
        per_token = F.cross_entropy(
            logits.reshape(-1, logits.size(-1)), y.reshape(-1), reduction="none"
        )
        preds = logits.argmax(dim=-1).reshape(-1)
        targets = y.reshape(-1)
        for i in range(targets.numel()):
            pos_loss_sum[i] += float(per_token[i].item())
            pos_count[i] += 1
            pos_correct[i] += int(preds[i].item() == targets[i].item())
        window_count += 1

    if was_training:
        model.train()

    total_loss = sum(pos_loss_sum)
    total_tokens = sum(pos_count)
    total_correct = sum(pos_correct)
    per_position_loss = [
        (pos_loss_sum[i] / pos_count[i]) if pos_count[i] else None for i in range(window_len)
    ]
    per_position_accuracy = [
        (pos_correct[i] / pos_count[i]) if pos_count[i] else None for i in range(window_len)
    ]
    return {
        "overall_loss": total_loss / total_tokens,
        "overall_token_accuracy": total_correct / total_tokens,
        "heldout_token_count": total_tokens,
        "heldout_window_count": window_count,
        "per_position_loss": per_position_loss,
        "per_position_count": list(pos_count),
        "per_position_accuracy": per_position_accuracy,
    }


def bucket_per_position(
    per_position_loss: list[float | None],
    per_position_count: list[int],
    *,
    lo: int,
    hi: int,
) -> tuple[float | None, int]:
    """Token-count-weighted mean loss over position indices ``[lo, hi)``.

    Returns ``(mean_loss_or_None, token_count)``; ``None`` when the bucket holds no
    tokens. Weighting by count makes this exactly equal to ``sum(CE)/sum(tokens)``
    over the bucket, so it composes back to the overall loss.
    """
    weighted = 0.0
    count = 0
    for i in range(max(lo, 0), min(hi, len(per_position_loss))):
        c = per_position_count[i]
        loss = per_position_loss[i]
        if c and loss is not None:
            weighted += loss * c
            count += c
    if count == 0:
        return None, 0
    return weighted / count, count


@torch.no_grad()
def evaluate_sliding_window(
    model: nn.Module,
    token_ids: list[int] | torch.Tensor,
    *,
    window_size: int,
    device: torch.device,
    batch_size: int = 256,
) -> dict[str, float | int]:
    """Score every next token using a sliding context window of ``window_size``.

    This is the *realistic* deployment of a learned-absolute-position model on a
    stream longer than its trained length: re-index each prediction into trained
    positions ``0 .. window_size-1`` by only ever feeding the last ``window_size``
    tokens. Each target at stream index ``t`` (for ``t >= window_size``) is
    predicted from tokens ``[t-window_size, t)`` — so no untrained position row is
    ever used. Targets ``t < window_size`` (the first ``window_size`` tokens) are
    excluded; they are a negligible fraction of a long stream.
    """
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    if isinstance(token_ids, torch.Tensor):
        data = token_ids.detach().to("cpu", dtype=torch.long)
    else:
        data = torch.tensor(list(token_ids), dtype=torch.long)
    if data.numel() <= window_size:
        raise ValueError("stream must be longer than window_size for sliding-window eval")

    was_training = model.training
    model.eval()

    windows = data.unfold(0, window_size, 1)[:-1]  # (N-window_size, window_size)
    targets = data[window_size:]  # (N-window_size,)
    total_loss = 0.0
    total_correct = 0
    total_tokens = 0
    for begin in range(0, windows.size(0), batch_size):
        x = windows[begin : begin + batch_size].to(device)
        y = targets[begin : begin + batch_size].to(device)
        logits, _ = model(x)
        last = logits[:, -1, :]
        per_token = F.cross_entropy(last, y, reduction="none")
        total_loss += float(per_token.sum().item())
        total_correct += int((last.argmax(dim=-1) == y).sum().item())
        total_tokens += int(y.numel())

    if was_training:
        model.train()

    return {
        "sliding_loss": total_loss / total_tokens,
        "sliding_token_accuracy": total_correct / total_tokens,
        "sliding_token_count": total_tokens,
        "window_size": window_size,
    }


__all__ = [
    "evaluate_heldout",
    "evaluate_heldout_per_position",
    "bucket_per_position",
    "evaluate_sliding_window",
]

"""Supervised fine-tuning (SFT) training loop with completion-only loss masking.

The defining mechanic of instruction tuning: a training example is a full
``prompt + completion`` sequence, but the loss is computed **only over the
completion tokens**. The prompt tokens (and padding) are masked out with
``ignore_index=-100`` so the model is supervised to *produce* the response, not
to reproduce the instruction. Set ``mask_prompt=False`` to recover the naive
full-sequence objective — v1164 uses that as the ablation baseline.

This complements :func:`minigpt.lm_training.train_lm` (plain next-token LM): same
AdamW spirit, but per-example padded batches with a masked target.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

IGNORE_INDEX = -100


def train_sft(
    model: nn.Module,
    examples: list[tuple[list[int], int]],
    *,
    steps: int,
    lr: float,
    batch_size: int,
    block_size: int,
    device: torch.device,
    pad_id: int,
    mask_prompt: bool = True,
    weight_decay: float | None = None,
    log_every: int | None = None,
    label: str = "sft",
) -> float:
    """Train ``model`` on SFT ``examples`` and return the last batch loss.

    Each example is ``(full_ids, n_prompt)`` where ``full_ids`` is the prompt
    followed by the completion and ``n_prompt`` is the prompt length. With
    ``mask_prompt=True`` (default) only completion-token predictions contribute to
    the loss; padding is always masked.
    """
    n = len(examples)
    if n == 0:
        raise ValueError("no SFT examples to train on")
    max_len = max(len(full) for full, _ in examples)
    if max_len - 1 > block_size:
        raise ValueError(f"block_size {block_size} too small for longest example ({max_len})")

    # Pre-tensorize once: X = padded inputs, Y = masked next-token targets.
    X = torch.full((n, block_size), pad_id, dtype=torch.long)
    Y = torch.full((n, block_size), IGNORE_INDEX, dtype=torch.long)
    for i, (full, n_prompt) in enumerate(examples):
        inp, tgt = full[:-1], full[1:]
        X[i, : len(inp)] = torch.tensor(inp, dtype=torch.long)
        for t, tok in enumerate(tgt):
            # tgt[t] predicts full[t+1]; supervise it unless it is a prompt token
            # (when mask_prompt) — completion starts at index n_prompt.
            if mask_prompt and (t + 1) < n_prompt:
                continue
            Y[i, t] = tok
    X, Y = X.to(device), Y.to(device)

    optimizer = (
        torch.optim.AdamW(model.parameters(), lr=lr)
        if weight_decay is None
        else torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    )
    model.train()
    last = float("nan")
    for step in range(1, steps + 1):
        sel = torch.randint(0, n, (batch_size,), device=device)
        x, y = X[sel], Y[sel]
        logits, _ = model(x)
        loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1), ignore_index=IGNORE_INDEX)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        last = float(loss.item())
        if log_every and (step == 1 or step % log_every == 0 or step == steps):
            print(f"[{label}] step={step:5d} loss={last:.4f}")
    return last


__all__ = ["train_sft", "IGNORE_INDEX"]

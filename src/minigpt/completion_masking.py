"""Shared completion-token masking helpers.

Several MiniGPT experiment families train or evaluate on examples shaped as
``(full_token_ids, prompt_length)``. The prompt is context; only completion
tokens should carry loss. Keeping the padded ``X`` / masked ``Y`` builder here
prevents each experiment from growing its own subtly different copy.
"""

from __future__ import annotations

import torch

from minigpt.sft_training import IGNORE_INDEX


def build_completion_xy(examples, block_size: int, pad_id: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Return padded ``X`` and completion-masked ``Y`` for tokenized examples."""
    n = len(examples)
    X = torch.full((n, block_size), pad_id, dtype=torch.long)
    Y = torch.full((n, block_size), IGNORE_INDEX, dtype=torch.long)
    for i, (full, n_prompt) in enumerate(examples):
        inp, tgt = full[:-1], full[1:]
        X[i, : len(inp)] = torch.tensor(inp, dtype=torch.long)
        for t, tok in enumerate(tgt):
            if (t + 1) < n_prompt:
                continue
            Y[i, t] = tok
    return X, Y


__all__ = ["build_completion_xy"]

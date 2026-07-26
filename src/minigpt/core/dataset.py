from __future__ import annotations

from pathlib import Path

import torch


def load_text(path: str | Path) -> str:
    text = Path(path).read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Training data is empty: {path}")
    return text


def split_token_ids(token_ids: list[int], train_ratio: float = 0.9) -> tuple[torch.Tensor, torch.Tensor]:
    if not 0.0 < train_ratio < 1.0:
        raise ValueError("train_ratio must be between 0 and 1")

    split_idx = max(1, int(len(token_ids) * train_ratio))
    train_ids = torch.tensor(token_ids[:split_idx], dtype=torch.long)
    val_ids = torch.tensor(token_ids[split_idx:], dtype=torch.long)
    if len(val_ids) < 2:
        val_ids = train_ids
    return train_ids, val_ids


def get_batch(
    data: torch.Tensor,
    block_size: int,
    batch_size: int,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
    if len(data) <= block_size + 1:
        raise ValueError(
            f"Dataset has {len(data)} tokens, but block_size={block_size}. "
            "Use more text or reduce --block-size."
        )

    max_start = len(data) - block_size - 1
    starts = torch.randint(0, max_start + 1, (batch_size,))
    x = torch.stack([data[i : i + block_size] for i in starts])
    y = torch.stack([data[i + 1 : i + block_size + 1] for i in starts])
    return x.to(device), y.to(device)

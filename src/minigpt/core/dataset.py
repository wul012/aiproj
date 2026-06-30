"""Compatibility exports for MiniGPT dataset helpers."""

from __future__ import annotations

from minigpt.dataset import get_batch, load_text, split_token_ids

__all__ = ["load_text", "split_token_ids", "get_batch"]


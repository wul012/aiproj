"""Stable core import surface for MiniGPT primitives.

The implementation still lives in the historical flat modules. This package
provides a migration target before the physical module move.
"""

from __future__ import annotations

from minigpt.core.dataset import get_batch, load_text, split_token_ids
from minigpt.core.history import TrainingRecord, append_record, load_records, summarize_records, write_loss_curve_svg
from minigpt.core.model import GPTConfig, MiniGPT, select_next_token
from minigpt.core.rope import apply_rope, build_rope_cache, rotate_half
from minigpt.core.tokenizer import BPETokenizer, CharTokenizer, Tokenizer, load_tokenizer

__all__ = [
    "GPTConfig",
    "MiniGPT",
    "select_next_token",
    "CharTokenizer",
    "BPETokenizer",
    "Tokenizer",
    "load_tokenizer",
    "load_text",
    "split_token_ids",
    "get_batch",
    "TrainingRecord",
    "append_record",
    "load_records",
    "summarize_records",
    "write_loss_curve_svg",
    "rotate_half",
    "build_rope_cache",
    "apply_rope",
]


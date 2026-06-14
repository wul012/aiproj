"""Shared scaffolding for the multi-seed capability experiments (v1164+).

The SFT / transfer / DPO experiment drivers (`sft_instruction_v1164`,
`sft_pretrain_transfer_v1165`, `dpo_preference_v1166`) all repeat the same three
primitives: aggregate a per-seed list into ``(mean, std)``, build a fresh
``MiniGPT`` from an experiment config, and snapshot a model's weights for a
later ``load_state_dict``. This module is the single home for them (extracted in
the v1167 maintenance pass, contract-preserving: each function reproduces the
prior inline behavior exactly).
"""

from __future__ import annotations

import math
import statistics
from typing import Any

import torch

from minigpt.model import GPTConfig, MiniGPT


def mean_std(values: list[float]) -> tuple[float, float]:
    """Mean and (sample) std of ``values``, ignoring ``None`` and ``NaN``.

    Returns ``(nan, 0.0)`` when nothing usable remains and ``std=0.0`` for a
    single value. NaN-filtering is harmless for inputs that never contain NaN
    (the v1164/v1165 callers), and necessary for v1166's ``last_loss`` column.
    """
    clean = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not clean:
        return float("nan"), 0.0
    return sum(clean) / len(clean), (statistics.stdev(clean) if len(clean) > 1 else 0.0)


def build_minigpt(vocab_size: int, config: Any, *, dropout: float = 0.0) -> MiniGPT:
    """Construct a fresh ``MiniGPT`` from an experiment ``config``.

    ``config`` only needs the attributes ``block_size``, ``n_layer``,
    ``n_head``, ``n_embd`` and ``use_rope`` (the shared fields of the v1164-v1166
    config dataclasses). The model is returned on CPU; callers move it to their
    device, exactly as the prior inline construction did, so the RNG stream and
    therefore the initialized weights are identical.
    """
    return MiniGPT(
        GPTConfig(
            vocab_size=vocab_size, block_size=config.block_size, n_layer=config.n_layer,
            n_head=config.n_head, n_embd=config.n_embd, dropout=dropout, use_rope=config.use_rope,
        )
    )


def clone_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    """A detached deep copy of ``model.state_dict()`` for a later
    ``load_state_dict`` (snapshotting a base / init checkpoint)."""
    return {k: v.detach().clone() for k, v in model.state_dict().items()}


__all__ = ["mean_std", "build_minigpt", "clone_state"]

"""Versioned RNG snapshots for step-boundary training continuation."""

from __future__ import annotations

import random
from typing import Any

import numpy as np
import torch


def capture_rng_state() -> dict[str, Any]:
    """Capture initialized generators without initializing a CUDA runtime."""
    return {
        "version": 1,
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None,
    }


def restore_rng_state(state: dict[str, Any] | None) -> bool:
    """Restore a snapshot after setup; missing legacy snapshots are a no-op.

    Serialized generator tensors must be on CPU even if torch.load mapped
    model tensors to CUDA. CUDA state is restored only to an initialized runtime.
    """
    if state is None:
        return False
    if state.get("version") != 1:
        raise ValueError("Unsupported checkpoint RNG state version")
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch_cpu"].cpu())
    if state["cuda"] is not None and torch.cuda.is_initialized():
        torch.cuda.set_rng_state_all([item.cpu() for item in state["cuda"]])
    return True

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


def validate_rng_state(state: dict[str, Any] | None) -> dict[str, Any] | None:
    """Validate on private CPU generators and return normalized state.

    CUDA payloads are structurally checked only; do not initialize devices to
    validate an optional snapshot. None preserves the legacy no-op contract.
    """
    if state is None:
        return None
    if not isinstance(state, dict) or type(state.get("version")) is not int or state["version"] != 1:
        raise ValueError("Unsupported checkpoint RNG state version")
    try:
        random.Random(0).setstate(state["python"])
        np.random.RandomState(0).set_state(state["numpy"])
        cpu = _state_tensor(state["torch_cpu"])
        torch.Generator(device="cpu").set_state(cpu)
        cuda = state["cuda"]
        if cuda is not None:
            if not isinstance(cuda, (list, tuple)):
                raise ValueError("cuda must be a sequence of generator tensors")
            cuda = [_state_tensor(item) for item in cuda]
    except (LookupError, TypeError, ValueError, RuntimeError, OverflowError) as exc:
        raise ValueError(f"Invalid checkpoint RNG state: {exc}") from exc
    return state | {"torch_cpu": cpu, "cuda": cuda}


def _state_tensor(value: Any) -> torch.Tensor:
    if not isinstance(value, torch.Tensor) or value.dtype != torch.uint8 or value.ndim != 1 or value.numel() == 0:
        raise ValueError("generator state must be a nonempty 1-D uint8 tensor")
    return value.cpu()


def restore_rng_state(state: dict[str, Any] | None) -> bool:
    """Reject malformed snapshots before touching globals; restore after setup."""
    state = validate_rng_state(state)
    if state is None:
        return False
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch_cpu"])
    if state["cuda"] is not None and torch.cuda.is_initialized():
        torch.cuda.set_rng_state_all(state["cuda"])
    return True

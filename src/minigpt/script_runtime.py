"""Shared entry-point helpers for the ``scripts/`` CLIs.

Extracted in v1163 to remove two copy-pasted fragments that accumulated across
the capability-pivot run scripts (v1156-v1162):

* ``choose_device`` — an identical device-selection helper that appeared in every
  ``run_*_v11xx`` script;
* ``seed_everything`` — the ``torch`` / ``numpy`` / ``random`` seeding triple the
  held-out-eval family runs before building a corpus and model.

Behavior matches those scripts exactly: ``choose_device`` raises ``SystemExit``
(a clean CLI error without a traceback) when ``cuda`` is requested but
unavailable. This is contract-preserving for the v1156-v1162 scripts; the older
legacy scripts keep their own device helper and are intentionally out of scope.
"""

from __future__ import annotations

import random

import numpy as np
import torch


def choose_device(name: str) -> torch.device:
    """Resolve a ``--device`` argument (``auto`` / ``cpu`` / ``cuda``)."""
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but torch.cuda.is_available() is False")
    return torch.device(name)


def seed_everything(seed: int) -> None:
    """Seed ``torch``, ``numpy``, and Python's ``random`` from one call."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)


__all__ = ["choose_device", "seed_everything"]

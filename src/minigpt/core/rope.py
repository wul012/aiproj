"""Rotary Position Embedding (RoPE) for MiniGPT attention.

RoPE encodes position by *rotating* query/key vectors by a position-dependent
angle, so attention scores depend on the relative offset between tokens rather
than on a learned absolute-position table. This module provides the small,
testable primitives; :class:`minigpt.model.CausalSelfAttention` applies them
when ``GPTConfig.use_rope`` is set.

Convention: the Llama / "rotate_half" form. For a head dimension ``hs`` (must be
even) and frequency base ``theta``:

    freqs[t, i] = t * theta**(-2i/hs)            i in [0, hs/2)
    emb         = concat(freqs, freqs)           shape (T, hs)
    rope(x)     = x * cos(emb) + rotate_half(x) * sin(emb)

The rotation is norm-preserving, which is what keeps attention well-scaled.
"""

from __future__ import annotations

import torch


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Map [x1, x2] -> [-x2, x1] over the last dim split in half."""
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat((-x2, x1), dim=-1)


def build_rope_cache(seq_len: int, head_size: int, *, base: float = 10000.0, device=None, dtype=torch.float32):
    """Return (cos, sin), each shape (seq_len, head_size), for RoPE."""
    if head_size % 2 != 0:
        raise ValueError(f"RoPE requires an even head size, got {head_size}")
    theta = 1.0 / (base ** (torch.arange(0, head_size, 2, device=device, dtype=dtype) / head_size))
    positions = torch.arange(seq_len, device=device, dtype=dtype)
    freqs = torch.outer(positions, theta)  # (seq_len, head_size/2)
    emb = torch.cat((freqs, freqs), dim=-1)  # (seq_len, head_size)
    return emb.cos(), emb.sin()


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    """Apply rotary embedding to ``x`` of shape (B, n_head, T, head_size).

    ``cos``/``sin`` are (T, head_size); they broadcast over batch and heads.
    """
    seq_len = x.shape[-2]
    cos = cos[:seq_len].to(dtype=x.dtype, device=x.device).view(1, 1, seq_len, -1)
    sin = sin[:seq_len].to(dtype=x.dtype, device=x.device).view(1, 1, seq_len, -1)
    return x * cos + rotate_half(x) * sin


__all__ = ["apply_rope", "build_rope_cache", "rotate_half"]

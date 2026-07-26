"""Transformer building blocks for MiniGPT.

Split out of the historical flat ``minigpt.model`` during the v1308 core
migration so each owner-package module stays under the 220-line cap. The
definitions are byte-identical to their originals; only their home changed.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.nn import functional as F

from minigpt.core.rope import apply_rope, build_rope_cache


@dataclass
class GPTConfig:
    vocab_size: int
    block_size: int = 128
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 128
    dropout: float = 0.1
    bias: bool = True
    use_rope: bool = False
    rope_base: float = 10000.0


class CausalSelfAttention(nn.Module):
    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        if config.n_embd % config.n_head != 0:
            raise ValueError("n_embd must be divisible by n_head")

        self.n_head = config.n_head
        self.head_size = config.n_embd // config.n_head
        self.c_attn = nn.Linear(config.n_embd, 3 * config.n_embd, bias=config.bias)
        self.c_proj = nn.Linear(config.n_embd, config.n_embd, bias=config.bias)
        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)
        self.capture_attention = False
        self.last_attention: torch.Tensor | None = None
        mask = torch.tril(torch.ones(config.block_size, config.block_size))
        self.register_buffer("causal_mask", mask.view(1, 1, config.block_size, config.block_size))

        self.use_rope = config.use_rope
        if self.use_rope:
            if self.head_size % 2 != 0:
                raise ValueError("RoPE requires n_embd / n_head to be even")
            cos, sin = build_rope_cache(config.block_size, self.head_size, base=config.rope_base)
            # Derived, non-persistent: kept out of state_dict so checkpoints stay clean.
            self.register_buffer("rope_cos", cos, persistent=False)
            self.register_buffer("rope_sin", sin, persistent=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, embd_size = x.shape
        q, k, v = self.c_attn(x).split(embd_size, dim=2)

        q = q.view(batch_size, seq_len, self.n_head, self.head_size).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.n_head, self.head_size).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.n_head, self.head_size).transpose(1, 2)

        if self.use_rope:
            q = apply_rope(q, self.rope_cos, self.rope_sin)
            k = apply_rope(k, self.rope_cos, self.rope_sin)

        att = (q @ k.transpose(-2, -1)) * (self.head_size**-0.5)
        att = att.masked_fill(self.causal_mask[:, :, :seq_len, :seq_len] == 0, float("-inf"))
        att = F.softmax(att, dim=-1)
        if self.capture_attention:
            self.last_attention = att.detach().cpu()
        else:
            self.last_attention = None

        y = self.attn_dropout(att) @ v
        y = y.transpose(1, 2).contiguous().view(batch_size, seq_len, embd_size)
        return self.resid_dropout(self.c_proj(y))

    def forward_cached(
        self,
        x: torch.Tensor,
        cache: tuple[torch.Tensor, torch.Tensor] | None,
        pos_offset: int,
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        """Incremental attention: ``x`` are the new tokens at absolute positions
        ``pos_offset .. pos_offset + T_new - 1``; ``cache`` holds past (k, v).

        Returns the attention output for the new tokens and the updated (k, v)
        cache. Math is identical to :meth:`forward` over the full sequence — this
        is verified by the v1161 logit-equality test.
        """
        batch_size, t_new, embd_size = x.shape
        q, k, v = self.c_attn(x).split(embd_size, dim=2)
        q = q.view(batch_size, t_new, self.n_head, self.head_size).transpose(1, 2)
        k = k.view(batch_size, t_new, self.n_head, self.head_size).transpose(1, 2)
        v = v.view(batch_size, t_new, self.n_head, self.head_size).transpose(1, 2)

        if self.use_rope:
            cos = self.rope_cos[pos_offset : pos_offset + t_new]
            sin = self.rope_sin[pos_offset : pos_offset + t_new]
            q = apply_rope(q, cos, sin)
            k = apply_rope(k, cos, sin)

        if cache is not None:
            past_k, past_v = cache
            k = torch.cat((past_k, k), dim=2)
            v = torch.cat((past_v, v), dim=2)
        new_cache = (k, v)

        t_total = k.shape[2]
        att = (q @ k.transpose(-2, -1)) * (self.head_size**-0.5)
        # Causal mask over absolute positions: query row i (abs pos_offset+i) may
        # attend key col j (abs j) iff j <= pos_offset + i.
        q_pos = torch.arange(pos_offset, pos_offset + t_new, device=x.device).view(t_new, 1)
        k_pos = torch.arange(0, t_total, device=x.device).view(1, t_total)
        att = att.masked_fill((k_pos > q_pos).view(1, 1, t_new, t_total), float("-inf"))
        att = F.softmax(att, dim=-1)

        y = self.attn_dropout(att) @ v
        y = y.transpose(1, 2).contiguous().view(batch_size, t_new, embd_size)
        return self.resid_dropout(self.c_proj(y)), new_cache


class MLP(nn.Module):
    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(config.n_embd, 4 * config.n_embd, bias=config.bias),
            nn.GELU(),
            nn.Linear(4 * config.n_embd, config.n_embd, bias=config.bias),
            nn.Dropout(config.dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class Block(nn.Module):
    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        self.ln_1 = nn.LayerNorm(config.n_embd, bias=config.bias)
        self.attn = CausalSelfAttention(config)
        self.ln_2 = nn.LayerNorm(config.n_embd, bias=config.bias)
        self.mlp = MLP(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln_1(x))
        x = x + self.mlp(self.ln_2(x))
        return x

    def forward_cached(
        self,
        x: torch.Tensor,
        cache: tuple[torch.Tensor, torch.Tensor] | None,
        pos_offset: int,
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        attn_out, new_cache = self.attn.forward_cached(self.ln_1(x), cache, pos_offset)
        x = x + attn_out
        x = x + self.mlp(self.ln_2(x))
        return x, new_cache


__all__ = ["GPTConfig", "CausalSelfAttention", "MLP", "Block"]

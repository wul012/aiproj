"""The MiniGPT model itself.

Building blocks live in :mod:`minigpt.core.layers`; this module keeps the
model, its sampling entry points and the shared token-selection helper.
``GPTConfig`` is re-exported so ``from minigpt.model import GPTConfig``
(and every historical caller) keeps working unchanged.
"""
from __future__ import annotations

import torch
import torch.nn as nn
from torch.nn import functional as F

from minigpt.core.layers import Block, GPTConfig


def select_next_token(
    last_logits: torch.Tensor,
    *,
    temperature: float = 1.0,
    top_k: int | None = None,
    blocked_token_ids: list[int] | None = None,
) -> torch.Tensor:
    """Sample one next token id (per batch row) from the final-position logits.

    Shared by :meth:`MiniGPT.sample_next` (uncached) and
    :meth:`MiniGPT.generate_cached` so both paths sample identically.
    """
    if temperature <= 0:
        raise ValueError("temperature must be greater than 0")
    logits = last_logits / temperature
    if blocked_token_ids:
        blocked = sorted({int(token_id) for token_id in blocked_token_ids if 0 <= int(token_id) < logits.size(-1)})
        if len(blocked) >= logits.size(-1):
            raise ValueError("blocked_token_ids cannot block every token")
        logits[:, blocked] = -float("inf")
    if top_k is not None:
        top_values, _ = torch.topk(logits, min(top_k, logits.size(-1)))
        logits[logits < top_values[:, [-1]]] = -float("inf")
    probs = F.softmax(logits, dim=-1)
    return torch.multinomial(probs, num_samples=1)


class MiniGPT(nn.Module):
    def __init__(self, config: GPTConfig) -> None:
        super().__init__()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.n_embd)
        self.position_embedding = nn.Embedding(config.block_size, config.n_embd)
        self.drop = nn.Dropout(config.dropout)
        self.blocks = nn.ModuleList([Block(config) for _ in range(config.n_layer)])
        self.ln_f = nn.LayerNorm(config.n_embd, bias=config.bias)
        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)
        self.lm_head.weight = self.token_embedding.weight

        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def features(self, idx: torch.Tensor) -> torch.Tensor:
        """Final hidden states (post-``ln_f``, pre-``lm_head``), shape
        ``(B, T, n_embd)``. Exposed for heads that read representations rather
        than token logits — e.g. the v1169 reward model's scalar head."""
        _, seq_len = idx.shape
        if seq_len > self.config.block_size:
            raise ValueError(f"Sequence length {seq_len} exceeds block_size {self.config.block_size}")

        x = self.token_embedding(idx)
        if not self.config.use_rope:
            positions = torch.arange(0, seq_len, dtype=torch.long, device=idx.device)
            x = x + self.position_embedding(positions)
        x = self.drop(x)
        for block in self.blocks:
            x = block(x)
        return self.ln_f(x)

    def forward(
        self,
        idx: torch.Tensor,
        targets: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        logits = self.lm_head(self.features(idx))

        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1))
        return logits, loss

    @torch.no_grad()
    def sample_next(
        self,
        idx: torch.Tensor,
        temperature: float = 1.0,
        top_k: int | None = None,
        blocked_token_ids: list[int] | None = None,
    ) -> torch.Tensor:
        if temperature <= 0:
            raise ValueError("temperature must be greater than 0")

        idx_cond = idx[:, -self.config.block_size :]
        logits, _ = self(idx_cond)
        return select_next_token(
            logits[:, -1, :], temperature=temperature, top_k=top_k, blocked_token_ids=blocked_token_ids
        )

    @torch.no_grad()
    def generate(
        self,
        idx: torch.Tensor,
        max_new_tokens: int,
        temperature: float = 1.0,
        top_k: int | None = None,
        blocked_token_ids: list[int] | None = None,
    ) -> torch.Tensor:
        if temperature <= 0:
            raise ValueError("temperature must be greater than 0")

        for _ in range(max_new_tokens):
            next_idx = self.sample_next(idx, temperature=temperature, top_k=top_k, blocked_token_ids=blocked_token_ids)
            idx = torch.cat((idx, next_idx), dim=1)
        return idx

    def forward_cached(
        self,
        idx: torch.Tensor,
        caches: list[tuple[torch.Tensor, torch.Tensor] | None] | None = None,
        pos_offset: int = 0,
    ) -> tuple[torch.Tensor, list[tuple[torch.Tensor, torch.Tensor]]]:
        """Forward only the new tokens ``idx`` at absolute positions starting at
        ``pos_offset``, reusing per-layer (k, v) ``caches``. Returns logits for the
        new tokens and the updated caches. Equivalent to :meth:`forward` over the
        full prefix, but without recomputing the cached positions.
        """
        _, t_new = idx.shape
        if pos_offset + t_new > self.config.block_size:
            raise ValueError(
                f"cached length {pos_offset + t_new} exceeds block_size {self.config.block_size}"
            )
        x = self.token_embedding(idx)
        if not self.config.use_rope:
            positions = torch.arange(pos_offset, pos_offset + t_new, dtype=torch.long, device=idx.device)
            x = x + self.position_embedding(positions)
        x = self.drop(x)
        if caches is None:
            caches = [None] * len(self.blocks)
        new_caches: list[tuple[torch.Tensor, torch.Tensor]] = []
        for block, cache in zip(self.blocks, caches):
            x, updated = block.forward_cached(x, cache, pos_offset)
            new_caches.append(updated)
        x = self.ln_f(x)
        logits = self.lm_head(x)
        return logits, new_caches

    @torch.no_grad()
    def generate_cached(
        self,
        idx: torch.Tensor,
        max_new_tokens: int,
        temperature: float = 1.0,
        top_k: int | None = None,
        blocked_token_ids: list[int] | None = None,
    ) -> torch.Tensor:
        """Same sampling contract as :meth:`generate`, but uses a KV cache so each
        new token costs one single-token forward instead of recomputing the whole
        sequence. Stops early if the context would exceed ``block_size``.
        """
        if temperature <= 0:
            raise ValueError("temperature must be greater than 0")
        self.eval()
        idx = idx[:, -self.config.block_size :]
        logits, caches = self.forward_cached(idx, None, 0)
        cur_len = idx.shape[1]
        for _ in range(max_new_tokens):
            next_idx = select_next_token(
                logits[:, -1, :], temperature=temperature, top_k=top_k, blocked_token_ids=blocked_token_ids
            )
            idx = torch.cat((idx, next_idx), dim=1)
            if cur_len >= self.config.block_size:
                break
            logits, caches = self.forward_cached(next_idx, caches, cur_len)
            cur_len += 1
        return idx

    def parameter_count(self) -> int:
        return sum(param.numel() for param in self.parameters())

    def set_attention_capture(self, enabled: bool) -> None:
        for block in self.blocks:
            block.attn.capture_attention = enabled
            if not enabled:
                block.attn.last_attention = None

    def attention_maps(self) -> list[torch.Tensor]:
        maps: list[torch.Tensor] = []
        for block in self.blocks:
            if block.attn.last_attention is not None:
                maps.append(block.attn.last_attention)
        return maps


__all__ = ["GPTConfig", "MiniGPT", "select_next_token"]

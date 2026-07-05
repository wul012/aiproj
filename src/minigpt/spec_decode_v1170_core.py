"""Core greedy and sampled speculative-decoding algorithms and diagnostics."""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

import torch

from minigpt.model import MiniGPT

# --------------------------------------------------------------------------
# shared selection rule (lowest-index argmax) — used by BOTH the plain
# reference and the spec verify so the only residual difference is the
# ~1e-7 logit drift (handled by the logit-identity gate + tie detector).
# --------------------------------------------------------------------------
def greedy_token(logits: torch.Tensor) -> torch.Tensor:
    """Argmax with a deterministic lowest-index tie-break. ``logits`` is ``(1, V)``."""
    m = logits.max(dim=-1, keepdim=True).values
    is_max = (logits >= m).to(torch.int8)
    return torch.argmax(is_max, dim=-1, keepdim=True)


def is_tie(logits: torch.Tensor, gap: float = 1e-5) -> bool:
    top2 = torch.topk(logits, 2, dim=-1).values
    return float((top2[0, 0] - top2[0, 1]).item()) < gap


def slice_caches(caches, length: int):
    """Truncate every per-layer (k, v) to ``length`` and make CONTIGUOUS so a
    rollback can never retain a view onto the larger (k+1)-wide allocation."""
    return [(k[:, :, :length, :].contiguous(), v[:, :, :length, :].contiguous()) for (k, v) in caches]


def _trunc_eos(tokens: list[int], eos_id: int) -> list[int]:
    return tokens[: tokens.index(eos_id)] if eos_id in tokens else tokens


@dataclass
class SpecStats:
    accepted: int = 0
    proposed: int = 0   # k per block (includes positions never tested after a reject)
    tested: int = 0     # acceptance tests actually performed (for the conditional alpha)
    blocks: int = 0
    target_forwards: int = 0
    draft_forwards: int = 0
    target_positions: int = 0  # FLOPs proxy: total positions fed to the target
    generated: int = 0


# --------------------------------------------------------------------------
# plain (non-speculative) greedy reference via the cached path, SAME selection
# --------------------------------------------------------------------------
@torch.no_grad()
def plain_generate_greedy(model: MiniGPT, prompt: torch.Tensor, *, max_new_tokens: int, block_size: int):
    model.eval()
    idx = prompt.clone()
    logits, caches = model.forward_cached(idx, None, 0)
    positions, forwards = idx.shape[1], 1
    last = logits[:, -1, :]
    cur = idx.shape[1]
    while idx.shape[1] - prompt.shape[1] < max_new_tokens:
        nxt = greedy_token(last)
        idx = torch.cat([idx, nxt], dim=1)
        if cur >= block_size:
            break
        logits, caches = model.forward_cached(nxt, caches, cur)
        last = logits[:, -1, :]
        positions += 1
        forwards += 1
        cur += 1
    return idx, positions, forwards


# --------------------------------------------------------------------------
# greedy speculative decoding with KV-cache rollback
# --------------------------------------------------------------------------
@torch.no_grad()
def speculative_generate_greedy(target: MiniGPT, draft: MiniGPT, prompt: torch.Tensor, *,
                                max_new_tokens: int, k: int, block_size: int):
    target.eval()
    draft.eval()
    idx = prompt.clone()
    L = idx.shape[1]
    stats = SpecStats()
    accept_by_pos: list[int] = []  # 1/0 per generated position (acceptance decay curve)

    if L >= 2:
        _, t_caches = target.forward_cached(idx[:, : L - 1], None, 0)
        _, d_caches = draft.forward_cached(idx[:, : L - 1], None, 0)
        stats.target_positions += L - 1
        stats.target_forwards += 1
        stats.draft_forwards += 1
    else:
        t_caches = d_caches = None

    while idx.shape[1] - prompt.shape[1] < max_new_tokens:
        L = idx.shape[1]
        a = idx[:, L - 1 : L]
        if L + k > block_size:  # keep the (k+1)-wide verify inside the context window
            break
        tokens = []
        cur, pos = a, L - 1
        for _ in range(k):
            dl, d_caches = draft.forward_cached(cur, d_caches, pos)
            pos += 1
            stats.draft_forwards += 1
            t = greedy_token(dl[:, -1, :])
            tokens.append(t)
            cur = t
        tl, t_caches = target.forward_cached(torch.cat([a] + tokens, dim=1), t_caches, L - 1)
        stats.target_forwards += 1
        stats.target_positions += k + 1
        stats.blocks += 1
        td = [tl[:, i, :] for i in range(k + 1)]

        n_accept = 0
        for i in range(k):
            ok = int(greedy_token(td[i]).item()) == int(tokens[i].item())
            accept_by_pos.append(int(ok))
            if ok:
                n_accept += 1
            else:
                break
        correction = greedy_token(td[n_accept])
        idx = torch.cat([idx] + tokens[:n_accept] + [correction], dim=1)
        stats.accepted += n_accept
        stats.proposed += k
        stats.tested += n_accept + (0 if n_accept == k else 1)  # +1 reject test unless all accepted

        keep = L + n_accept
        t_caches = slice_caches(t_caches, keep)
        if n_accept == k:  # full accept: draft never consumed tokens[k-1]; feed it before slicing
            _, d_caches = draft.forward_cached(tokens[k - 1], d_caches, L + k - 1)
            stats.draft_forwards += 1
        d_caches = slice_caches(d_caches, keep)

    idx = idx[:, : prompt.shape[1] + max_new_tokens]
    stats.generated = idx.shape[1] - prompt.shape[1]
    return idx, stats, accept_by_pos


# --------------------------------------------------------------------------
# speculative SAMPLING (rejection rule) + plain sampling reference
# --------------------------------------------------------------------------
@torch.no_grad()
def speculative_generate_sample(target: MiniGPT, draft: MiniGPT, prompt: torch.Tensor, *,
                                max_new_tokens: int, k: int, block_size: int,
                                temperature: float, generator: torch.Generator):
    target.eval()
    draft.eval()
    idx = prompt.clone()
    L = idx.shape[1]
    stats = SpecStats()
    if L >= 2:
        _, t_caches = target.forward_cached(idx[:, : L - 1], None, 0)
        _, d_caches = draft.forward_cached(idx[:, : L - 1], None, 0)
    else:
        t_caches = d_caches = None

    def probs(logits):
        return torch.softmax(logits / temperature, dim=-1)

    while idx.shape[1] - prompt.shape[1] < max_new_tokens:
        L = idx.shape[1]
        a = idx[:, L - 1 : L]
        if L + k > block_size:
            break
        tokens, draft_p = [], []
        cur, pos = a, L - 1
        for _ in range(k):
            dl, d_caches = draft.forward_cached(cur, d_caches, pos)
            pos += 1
            stats.draft_forwards += 1
            p = probs(dl[:, -1, :])
            t = torch.multinomial(p, 1, generator=generator)
            tokens.append(t)
            draft_p.append(p)
            cur = t
        tl, t_caches = target.forward_cached(torch.cat([a] + tokens, dim=1), t_caches, L - 1)
        stats.target_forwards += 1
        stats.target_positions += k + 1
        stats.blocks += 1
        target_q = [probs(tl[:, i, :]) for i in range(k + 1)]

        n_accept, emitted = 0, []
        for i in range(k):
            ti = int(tokens[i].item())
            ratio = torch.clamp(target_q[i][0, ti] / (draft_p[i][0, ti] + 1e-12), max=1.0)
            u = torch.rand((), generator=generator, device=ratio.device)
            if u <= ratio:
                emitted.append(tokens[i])
                n_accept += 1
            else:
                resid = torch.clamp(target_q[i] - draft_p[i], min=0.0)
                resid = resid / resid.sum(dim=-1, keepdim=True)
                emitted.append(torch.multinomial(resid, 1, generator=generator))
                break
        if n_accept == k:
            emitted.append(torch.multinomial(target_q[k], 1, generator=generator))
        idx = torch.cat([idx] + emitted, dim=1)
        stats.accepted += n_accept
        stats.proposed += k
        stats.tested += n_accept + (0 if n_accept == k else 1)  # +1 reject test unless all accepted

        keep = L + n_accept
        t_caches = slice_caches(t_caches, keep)
        if n_accept == k:
            _, d_caches = draft.forward_cached(tokens[k - 1], d_caches, L + k - 1)
            stats.draft_forwards += 1
        d_caches = slice_caches(d_caches, keep)

    idx = idx[:, : prompt.shape[1] + max_new_tokens]
    stats.generated = idx.shape[1] - prompt.shape[1]
    return idx, stats


@torch.no_grad()
def plain_sample(model: MiniGPT, prompt: torch.Tensor, *, max_new_tokens: int, block_size: int,
                 temperature: float, generator: torch.Generator):
    model.eval()
    idx = prompt.clone()
    logits, caches = model.forward_cached(idx, None, 0)
    cur = idx.shape[1]
    while idx.shape[1] - prompt.shape[1] < max_new_tokens:
        p = torch.softmax(logits[:, -1, :] / temperature, dim=-1)
        nxt = torch.multinomial(p, 1, generator=generator)
        idx = torch.cat([idx, nxt], dim=1)
        if cur >= block_size:
            break
        logits, caches = model.forward_cached(nxt, caches, cur)
        cur += 1
    return idx[:, : prompt.shape[1] + max_new_tokens]


# --------------------------------------------------------------------------
# correctness instruments
# --------------------------------------------------------------------------
@torch.no_grad()
def chunked_forward_logit_diff(model: MiniGPT, idx: torch.Tensor, chunk: int) -> float:
    """Max abs logit diff between the full forward over ``idx`` and a replay in
    ``chunk``-wide cached forwards — the v1161 cache invariant at verify width.
    ``chunk = k+1`` is exactly what the verify forward does numerically."""
    full, _ = model(idx)
    caches = None
    pos, T, mx = 0, idx.shape[1], 0.0
    while pos < T:
        w = min(chunk, T - pos)
        cl, caches = model.forward_cached(idx[:, pos : pos + w], caches, pos)
        mx = max(mx, float((cl - full[:, pos : pos + w, :]).abs().max().item()))
        pos += w
    return mx


@torch.no_grad()
def classify_greedy_diff(target: MiniGPT, plain_idx: torch.Tensor, spec_idx: torch.Tensor,
                         prompt_len: int, eos_id: int, gap: float = 1e-5) -> str:
    """``identical`` / ``tie_artifact`` (first diff sits at a logit tie) / ``genuine_diff``,
    comparing EOS-truncated completions (matching how the SFT corpus is consumed)."""
    p = _trunc_eos(plain_idx[0].tolist()[prompt_len:], eos_id)
    s = _trunc_eos(spec_idx[0].tolist()[prompt_len:], eos_id)
    if p == s:
        return "identical"
    full, _ = target(plain_idx)
    for i in range(min(len(p), len(s))):
        if p[i] != s[i]:
            logit_pos = prompt_len + i - 1
            if 0 <= logit_pos < full.shape[1] and is_tie(full[:, logit_pos, :], gap):
                return "tie_artifact"
            return "genuine_diff"
    return "genuine_diff"  # length-only mismatch


def _tv(a: torch.Tensor, b: torch.Tensor) -> float:
    pa, pb = a / a.sum(), b / b.sum()
    return 0.5 * float((pa - pb).abs().sum().item())


@torch.no_grad()
def _token_hist(seqs: list[list[int]], vocab: int) -> torch.Tensor:
    counts = torch.zeros(vocab)
    for s in seqs:
        for tok in s:
            counts[tok] += 1
    return counts


# --------------------------------------------------------------------------
# timing harness (B5): R repeats, warmup discarded, CUDA-synced
# --------------------------------------------------------------------------
def _sync(device):
    if device.type == "cuda":
        torch.cuda.synchronize()


def _time(fn, device, repeats: int, warmup: int) -> list[float]:
    for _ in range(warmup):
        fn()
    out = []
    for _ in range(repeats):
        _sync(device)
        t0 = time.perf_counter()
        fn()
        _sync(device)
        out.append(time.perf_counter() - t0)
    return out


def _median_iqr(xs: list[float]) -> tuple[float, float]:
    s = sorted(xs)
    n = len(s)
    return statistics.median(s), (s[(3 * n) // 4] - s[n // 4] if n >= 4 else 0.0)

__all__ = [
    "SpecStats",
    "chunked_forward_logit_diff",
    "classify_greedy_diff",
    "greedy_token",
    "is_tie",
    "plain_generate_greedy",
    "plain_sample",
    "slice_caches",
    "speculative_generate_greedy",
    "speculative_generate_sample",
]

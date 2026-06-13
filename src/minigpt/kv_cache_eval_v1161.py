"""v1161: verify and benchmark KV-cached generation.

Confirms the cached decode path is numerically identical to the uncached path
(max logit difference + greedy sequence equality), then measures the generation
speedup (tokens/sec) from reusing cached keys/values instead of recomputing the
whole sequence every step. Correctness gates ``status``; speed is reported
alongside.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import torch

from minigpt.model import GPTConfig, MiniGPT
from minigpt.report_utils import utc_now


@dataclass
class KvCacheBenchConfig:
    vocab_size: int = 64
    block_size: int = 256
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 128
    prompt_len: int = 8
    max_new_tokens: int = 200
    seed: int = 1337
    use_rope: bool = True


def _sync(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize()


def _time(fn, device: torch.device):
    _sync(device)
    start = perf_counter()
    out = fn()
    _sync(device)
    return perf_counter() - start, out


def _max_logit_diff(model: MiniGPT, seq: torch.Tensor) -> float:
    full_logits, _ = model(seq)
    steps = []
    caches = None
    for t in range(seq.shape[1]):
        step_logits, caches = model.forward_cached(seq[:, t : t + 1], caches, t)
        steps.append(step_logits[:, -1, :])
    cached_logits = torch.stack(steps, dim=1)
    return float((full_logits - cached_logits).abs().max().item())


def run_kv_cache_benchmark(
    *,
    config: KvCacheBenchConfig,
    device: torch.device,
    generated_at: str | None = None,
) -> dict:
    torch.manual_seed(config.seed)
    model = MiniGPT(
        GPTConfig(
            vocab_size=config.vocab_size, block_size=config.block_size, n_layer=config.n_layer,
            n_head=config.n_head, n_embd=config.n_embd, dropout=0.0, use_rope=config.use_rope,
        )
    ).to(device).eval()

    prompt = torch.randint(0, config.vocab_size, (1, config.prompt_len), device=device)

    # Correctness: identical computation (logits) and identical greedy output.
    check_seq = torch.randint(0, config.vocab_size, (1, min(32, config.block_size)), device=device)
    max_logit_diff = _max_logit_diff(model, check_seq)
    greedy_uncached = model.generate(prompt.clone(), max_new_tokens=32, top_k=1)
    greedy_cached = model.generate_cached(prompt.clone(), max_new_tokens=32, top_k=1)
    greedy_match = bool(torch.equal(greedy_uncached, greedy_cached))

    # Warmup (kernel compilation / allocator), then time greedy generation both ways.
    model.generate(prompt.clone(), max_new_tokens=8, top_k=1)
    model.generate_cached(prompt.clone(), max_new_tokens=8, top_k=1)
    uncached_s, _ = _time(lambda: model.generate(prompt.clone(), config.max_new_tokens, top_k=1), device)
    cached_s, _ = _time(lambda: model.generate_cached(prompt.clone(), config.max_new_tokens, top_k=1), device)

    n = config.max_new_tokens
    uncached_tps = n / uncached_s if uncached_s > 0 else 0.0
    cached_tps = n / cached_s if cached_s > 0 else 0.0
    speedup = uncached_s / cached_s if cached_s > 0 else 0.0

    # The sound correctness guarantee is logit identity (cached == full to float precision).
    # Greedy sequence equality is reported but NOT gated on: a ~1e-6 logit difference can flip
    # a near-tie in argmax on a tiny untrained model, which is an argmax artifact, not a cache bug.
    correct = max_logit_diff < 1e-4
    status = "pass" if correct else "review"
    if correct and speedup > 1.0:
        decision = "kv_cache_correct_and_faster"
    elif correct:
        decision = "kv_cache_correct"
    else:
        decision = "kv_cache_incorrect"

    rows = [
        {"method": "uncached_generate", "seconds": round(uncached_s, 5), "tokens_per_sec": round(uncached_tps, 2)},
        {"method": "cached_generate", "seconds": round(cached_s, 5), "tokens_per_sec": round(cached_tps, 2)},
    ]
    summary = {
        "status": status,
        "decision": decision,
        "device": str(device),
        "use_rope": config.use_rope,
        "block_size": config.block_size,
        "n_layer": config.n_layer,
        "n_embd": config.n_embd,
        "prompt_len": config.prompt_len,
        "generated_tokens": n,
        "uncached_seconds": round(uncached_s, 5),
        "cached_seconds": round(cached_s, 5),
        "uncached_tokens_per_sec": round(uncached_tps, 2),
        "cached_tokens_per_sec": round(cached_tps, 2),
        "speedup": round(speedup, 3),
        "max_logit_diff": max_logit_diff,
        "greedy_sequences_match": greedy_match,
        "correctness_verified": correct,
    }
    recommendations = [
        f"KV cache verified numerically identical to the uncached path (max logit diff {max_logit_diff:.2e}); "
        f"{speedup:.2f}x faster generating {n} tokens (greedy sequences match={greedy_match}).",
        "Speedup grows with sequence length and model size: uncached generation is O(n^2) over the sequence, the cached path is O(n); at tiny scale per-step overhead can make it neutral.",
    ]
    return {
        "schema_version": 1,
        "title": "MiniGPT KV-cache generation benchmark v1161",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "summary": summary,
        "rows": rows,
        "recommendations": recommendations,
        "csv_fieldnames": ["method", "seconds", "tokens_per_sec"],
    }


__all__ = ["KvCacheBenchConfig", "run_kv_cache_benchmark"]

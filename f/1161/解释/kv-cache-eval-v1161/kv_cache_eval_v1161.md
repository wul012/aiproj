# MiniGPT KV-cache generation benchmark v1161

- Generated: `2026-06-13T14:32:44Z`
- Status: `pass`
- Decision: `kv_cache_correct_and_faster`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | kv_cache_correct_and_faster |
| device | cuda |
| use_rope | True |
| block_size | 1024 |
| n_layer | 8 |
| n_embd | 512 |
| prompt_len | 8 |
| generated_tokens | 700 |
| uncached_seconds | 10.11139 |
| cached_seconds | 6.40909 |
| uncached_tokens_per_sec | 69.23 |
| cached_tokens_per_sec | 109.22 |
| speedup | 1.578 |
| max_logit_diff | 1.0728836059570312e-06 |
| greedy_sequences_match | True |
| correctness_verified | True |

## Rows

| method | seconds | tokens_per_sec |
| --- | --- | --- |
| uncached_generate | 10.11139 | 69.23 |
| cached_generate | 6.40909 | 109.22 |

## Recommendations

- KV cache verified numerically identical to the uncached path (max logit diff 1.07e-06); 1.58x faster generating 700 tokens (greedy sequences match=True).
- Speedup grows with sequence length and model size: uncached generation is O(n^2) over the sequence, the cached path is O(n); at tiny scale per-step overhead can make it neutral.

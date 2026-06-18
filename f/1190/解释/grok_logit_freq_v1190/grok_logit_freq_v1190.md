# MiniGPT v1190 grokking logit-frequency alignment

- Generated: `2026-06-18T08:01:34Z`
- Status: `pass`
- Decision: `embedding_logit_frequency_alignment_supports_trig_addition`

## Summary

| Metric | Value |
| --- | --- |
| checkpoint | D:\aiproj\f\1185\解释\grok_checkpoint_v1185\grok_checkpoint_v1185.pt |
| p | 97 |
| heldout_acc | 0.965989 |
| embedding_top_freqs | 43, 3, 48, 26, 44 |
| embedding_top_k_fraction | 0.305171 |
| embedding_dominant_freq | 43 |
| logit_top_freqs | 43, 3, 48, 26, 44 |
| logit_top_k_diagonal_fraction | 0.610591 |
| logit_diagonal_fraction | 0.718712 |
| random_logit_diagonal_fraction | 0.000122 |
| ideal_logit_diagonal_fraction | 1.0 |
| embedding_logit_top_freq_overlap_count | 5 |
| embedding_logit_top_freq_overlap_fraction | 1.0 |
| embedding_logit_top_freq_overlap | 3, 26, 43, 44, 48 |
| boundary | toy_scale_single_checkpoint_embedding_logit_frequency_alignment_not_a_scaling_claim |

## Logit Frequency Arms

| arm | diagonal_fraction | top_k_diagonal_fraction | dominant_freq | top_freqs |
| --- | --- | --- | --- | --- |
| shipped_checkpoint_logits | 0.718712 | 0.610591 | 43 | 43, 3, 48, 26, 44 |
| random_init_logits | 0.000122 | 0.20703 | 19 | 19, 21, 14, 31, 33 |
| ideal_addition_target | 1.0 | 0.104167 | 2 | 2, 1, 15, 22, 27 |

## Recommendations

- The shipped grokking checkpoint's output logits are concentrated on the diagonal 2D FFT frequencies expected for a+b=y modular addition surfaces.
- The logit dominant frequencies [43, 3, 48, 26, 44] align with the embedding dominant frequencies [43, 3, 48, 26, 44], supporting the trig-identity mechanism behind v1188.

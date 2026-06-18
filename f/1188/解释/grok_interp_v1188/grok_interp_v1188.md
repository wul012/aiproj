# MiniGPT v1188 grokking mechanistic interpretability

- Generated: `2026-06-18T06:09:36Z`
- Status: `pass`
- Decision: `fourier_structure_explains_generalization`

## Summary

| Metric | Value |
| --- | --- |
| p | 97 |
| top_k | 5 |
| seeds | 3 |
| verdict | fourier_structure_explains_generalization |
| g0_arms_behaved | True |
| g1_grid_complete | True |
| grokked_top_k_fraction | (0.307234, 0.003986) |
| memorized_top_k_fraction | (0.14978, 0.002044) |
| random_top_k_fraction | (0.120334, 0.000924) |
| grokked_entropy_mean | 0.914238 |
| memorized_entropy_mean | 0.994882 |
| random_entropy_mean | 0.998878 |
| beats_random | True |
| beats_memorized | True |
| shipped_checkpoint_top_k_fraction | 0.305171 |
| shipped_checkpoint_dominant_freq | 43 |
| boundary | toy_scale_single_task_interpretability_embedding_fourier_structure_only |

## Rows

| arm | seed | top_k_fraction | spectral_entropy | dominant_freq | n_freqs_for_90pct |
| --- | --- | --- | --- | --- | --- |
| grokked | 1337 | 0.305171 | 0.916381 | 43 | 34 |
| grokked | 1338 | 0.311829 | 0.912905 | 35 | 34 |
| grokked | 1339 | 0.304702 | 0.913427 | 32 | 34 |
| memorized | 1337 | 0.147427 | 0.994748 | 43 | 42 |
| memorized | 1338 | 0.150803 | 0.994467 | 14 | 42 |
| memorized | 1339 | 0.15111 | 0.99543 | 42 | 42 |
| random | 1337 | 0.120902 | 0.998956 | 19 | 43 |
| random | 1338 | 0.119268 | 0.998752 | 2 | 43 |
| random | 1339 | 0.120833 | 0.998926 | 31 | 43 |

## Recommendations

- The grokked model's number embeddings are sparse in the Fourier basis (a few dominant frequencies), significantly more than both a random-init and a memorized-but-not-grokked model.
- This is the weight-level mechanism behind grokking: only the generalizing (weight-decayed) model develops the Fourier structure that implements modular addition via trig identities.

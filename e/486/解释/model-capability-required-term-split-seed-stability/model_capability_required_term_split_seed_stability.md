# MiniGPT Model Capability Required-Term Split Seed Stability

- Status: `pass`
- Decision: `required_term_seed_stability_train_slice_partial`
- Seed stability decision: `train_slice_uptake_partial_without_holdout`
- Best split: `split-4`
- Holdout terms: `four, while`
- Train-repro seeds: `1` / `3`
- Holdout-hit seeds: `0`

| Seed | Train hits | Holdout hits | Decision |
| ---: | ---: | ---: | --- |
| 785 | 4 | 0 | training_slice_only_without_holdout_uptake |
| 1785 | 0 | 0 | heldout_micro_training_no_required_term_uptake |
| 2785 | 0 | 0 | heldout_micro_training_no_required_term_uptake |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Only some repeated seeds reproduced train-slice uptake, and held-out uptake stayed at zero.
- Next action: improve corpus construction before further held-out checks

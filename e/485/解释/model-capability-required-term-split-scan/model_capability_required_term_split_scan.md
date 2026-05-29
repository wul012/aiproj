# MiniGPT Model Capability Required-Term Split Scan

- Status: `pass`
- Decision: `required_term_split_scan_train_slice_only`
- Split scan decision: `train_slice_uptake_reproduced_without_holdout`
- Splits: `4`
- Train-repro splits: `2`
- Holdout-hit splits: `0`
- Best split: `split-4`

| Split | Holdout terms | Train hits | Holdout hits | Decision |
| --- | --- | ---: | ---: | --- |
| split-1 | because, fixed, real | 0 | 0 | heldout_micro_training_no_required_term_uptake |
| split-2 | chain, four, text | 4 | 0 | training_slice_only_without_holdout_uptake |
| split-3 | data, loss, while | 0 | 0 | heldout_micro_training_no_required_term_uptake |
| split-4 | four, while | 4 | 0 | training_slice_only_without_holdout_uptake |

## Boundary

- Model quality claim: `not_claimed`
- Reason: At least one split reproduced train-slice uptake, but no split produced held-out required-term uptake.
- Next action: stabilize the best train-slice split across seeds, then reintroduce a stricter holdout

# MiniGPT Required-Term Pair First-Token Route Decision

- Status: `pass`
- Decision: `stop_first_token_density_and_replay_best_baseline`
- Source reports: `3`
- First-token density routes: `2`
- Stable routes: `0`
- Selected route: `v562-loss-balanced`
- Source comparison: `e\567\解释\model-capability-required-term-pair-no-pair-id-first-token-density-comparison\model_capability_required_term_pair_equals_surface_repair_comparison.json`

## Selected Route

| Label | Corpus mode | Pair-full seeds | Stable | Rationale |
| --- | --- | ---: | --- | --- |
| v562-loss-balanced | equals_surface_no_pair_id_loss_balanced_repair | 1/3 | False | highest pair-full seed count with the simplest non-first-token-density objective |

## Rejected Routes

| Label | Corpus mode | Pair-full seeds | Reasons |
| --- | --- | ---: | --- |
| v564-full-first-token | equals_surface_no_pair_id_loss_balanced_first_token_repair | 1/3 | first_token_density_no_stable_gain,not_stable_across_seeds |
| v566-light-first-token | equals_surface_no_pair_id_loss_balanced_light_first_token_repair | 0/3 | first_token_density_no_stable_gain,no_pair_full_seed,not_stable_across_seeds |

## Boundary

- Model quality claim: `route_decision_only`
- Reason: First-token density variants do not improve stable pair-full coverage over the simpler baseline.
- Next action: replay held-out equals-surface prompts for v562-loss-balanced before adding more corpus variants

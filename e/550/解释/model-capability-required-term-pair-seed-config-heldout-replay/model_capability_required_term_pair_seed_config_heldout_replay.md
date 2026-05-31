# MiniGPT Required-Term Pair Seed Config Held-Out Replay

- Status: `pass`
- Decision: `required_term_pair_seed_config_heldout_replay_partial`
- Held-out pair-full rows: `8/9`
- Held-out all pair-full: `False`

## Replay Rows

| Spec | Seed | Config | Replay full | Default full | Suppression full |
| --- | ---: | --- | --- | ---: | ---: |
| colon-spaced | 535 | v544-topk2-t080 | True | 1 | 1 |
| equals | 535 | v544-topk2-t080 | True | 1 | 1 |
| arrow | 535 | v544-topk2-t080 | True | 1 | 1 |
| colon-spaced | 1535 | v546-loss-calibrated-topk2-t080 | True | 0 | 1 |
| equals | 1535 | v546-loss-calibrated-topk2-t080 | False | 0 | 0 |
| arrow | 1535 | v546-loss-calibrated-topk2-t080 | True | 1 | 1 |
| colon-spaced | 2535 | v544-topk2-t080 | True | 1 | 1 |
| equals | 2535 | v544-topk2-t080 | True | 1 | 0 |
| arrow | 2535 | v544-topk2-t080 | True | 1 | 1 |

## Boundary

- Reason: Some selected config held-out prompt surfaces replayed pair-full coverage, but the policy is not broadly robust.
- Next action: inspect which prompt surfaces transfer before adding more training variants

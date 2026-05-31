# MiniGPT Required-Term Pair Seed Config Replay

- Status: `pass`
- Decision: `required_term_pair_seed_config_replay_ready`
- Replay pair-full seeds: `3/3`
- Selected replay ready: `True`

## Replay Rows

| Seed | Selected config | Replay full | Default full | Suppression full |
| ---: | --- | --- | ---: | ---: |
| 535 | v544-topk2-t080 | True | 1 | 1 |
| 1535 | v546-loss-calibrated-topk2-t080 | True | 0 | 1 |
| 2535 | v544-topk2-t080 | True | 1 | 1 |

## Boundary

- Reason: Every selected per-seed config replayed pair-full coverage from its source checkpoint.
- Next action: test selected configs against held-out prompt variants or fresh seeds

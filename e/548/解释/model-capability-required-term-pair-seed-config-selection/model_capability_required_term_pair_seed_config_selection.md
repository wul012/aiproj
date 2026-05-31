# MiniGPT Required-Term Pair Seed Config Selection

- Status: `pass`
- Decision: `required_term_pair_seed_config_selection_multi_config_ready`
- Ready seeds: `3/3`
- Selected configs: `v544-topk2-t080, v546-loss-calibrated-topk2-t080`
- Multi-config policy: `True`

## Selections

| Seed | Selected config | Ready | Covering configs |
| ---: | --- | --- | --- |
| 535 | v544-topk2-t080 | True | v544-topk2-t080 |
| 1535 | v546-loss-calibrated-topk2-t080 | True | v546-loss-calibrated-topk2-t080 |
| 2535 | v544-topk2-t080 | True | v544-topk2-t080 |

## Boundary

- Reason: Every seed has a verified selected config, and more than one config is needed.
- Next action: test this explicit config-selection policy against held-out prompts or fresh seeds

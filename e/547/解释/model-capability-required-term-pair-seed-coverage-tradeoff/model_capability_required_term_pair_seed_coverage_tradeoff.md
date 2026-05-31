# MiniGPT Required-Term Pair Seed Coverage Tradeoff

- Status: `pass`
- Decision: `required_term_pair_seed_coverage_tradeoff_complementary_full_union`
- Union pair-full seeds: `3/3`
- Best single config: `v544-topk2-t080`
- Best single pair-full seeds: `2`
- Tradeoff detected: `True`

## Configs

| Config | Pair-full seeds | Seed count | Corpus | Decode |
| --- | ---: | ---: | --- | --- |
| v544-topk2-t080 | 2 | 3 | colon_immediate | k=2 t=0.8 |
| v546-loss-calibrated-topk2-t080 | 1 | 3 | colon_immediate_loss_calibrated | k=2 t=0.8 |

## Seeds

| Seed | Covered | Winning config | Covering configs |
| ---: | --- | --- | --- |
| 535 | True | v544-topk2-t080 | v544-topk2-t080 |
| 1535 | True | v546-loss-calibrated-topk2-t080 | v546-loss-calibrated-topk2-t080 |
| 2535 | True | v544-topk2-t080 | v544-topk2-t080 |

## Boundary

- Reason: No single configuration covers every seed, but the compared configurations cover all seeds together.
- Next action: test an explicit fallback or config-selection policy before more corpus changes

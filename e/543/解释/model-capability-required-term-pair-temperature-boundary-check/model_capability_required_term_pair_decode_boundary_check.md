# MiniGPT Required-Term Pair Decode Boundary Check

- Status: `pass`
- Decision: `required_term_pair_decode_boundary_improves_pair_surface`
- Baseline pair-full seeds: `1`
- Best spec: `topk2-t080-n12`
- Best pair-full seeds: `2`

## Rows

| Spec | Seed | Pair full | Default hits | Suppression hits | Decision |
| --- | ---: | --- | ---: | ---: | --- |
| greedy-k1-t020-n12 | 535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| greedy-k1-t020-n12 | 1535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| greedy-k1-t020-n12 | 2535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| topk2-t040-n12 | 535 | True | 2 | 2 | generation_profile_no_pair_coexistence_gain |
| topk2-t040-n12 | 1535 | False | 0 | 0 | generation_profile_no_pair_coexistence_gain |
| topk2-t040-n12 | 2535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| topk2-t080-n12 | 535 | True | 2 | 2 | generation_profile_no_pair_coexistence_gain |
| topk2-t080-n12 | 1535 | False | 0 | 0 | generation_profile_no_pair_coexistence_gain |
| topk2-t080-n12 | 2535 | True | 2 | 2 | generation_profile_no_pair_coexistence_gain |
| topk2-t120-n12 | 535 | True | 2 | 2 | generation_profile_no_pair_coexistence_gain |
| topk2-t120-n12 | 1535 | False | 0 | 0 | generation_profile_no_pair_coexistence_gain |
| topk2-t120-n12 | 2535 | False | 0 | 0 | generation_profile_no_pair_coexistence_gain |
| topk4-t080-n12 | 535 | True | 1 | 2 | generation_profile_improves_pair_coexistence |
| topk4-t080-n12 | 1535 | False | 0 | 0 | generation_profile_no_pair_coexistence_gain |
| topk4-t080-n12 | 2535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |

## Boundary

- Reason: At least one decode boundary improves pair-full coverage over the source stability report.
- Next action: promote the best decode spec into the next stability check before retraining

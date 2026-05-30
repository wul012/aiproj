# MiniGPT Required-Term Pair Decode Boundary Check

- Status: `pass`
- Decision: `required_term_pair_decode_boundary_improves_pair_surface`
- Baseline pair-full seeds: `0`
- Best spec: `wider-k2-t020-n12`
- Best pair-full seeds: `1`

## Rows

| Spec | Seed | Pair full | Default hits | Suppression hits | Decision |
| --- | ---: | --- | ---: | ---: | --- |
| greedy-k1-t020-n12 | 535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| greedy-k1-t020-n12 | 1535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| greedy-k1-t020-n12 | 2535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| wider-k2-t020-n12 | 535 | True | 2 | 2 | generation_profile_no_pair_coexistence_gain |
| wider-k2-t020-n12 | 1535 | False | 0 | 0 | generation_profile_no_pair_coexistence_gain |
| wider-k2-t020-n12 | 2535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| wider-k4-t020-n12 | 535 | True | 2 | 2 | generation_profile_no_pair_coexistence_gain |
| wider-k4-t020-n12 | 1535 | False | 0 | 0 | generation_profile_no_pair_coexistence_gain |
| wider-k4-t020-n12 | 2535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| greedy-k1-t020-n20 | 535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| greedy-k1-t020-n20 | 1535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |
| greedy-k1-t020-n20 | 2535 | False | 1 | 1 | generation_profile_no_pair_coexistence_gain |

## Boundary

- Reason: At least one decode boundary improves pair-full coverage over the source stability report.
- Next action: promote the best decode spec into the next stability check before retraining

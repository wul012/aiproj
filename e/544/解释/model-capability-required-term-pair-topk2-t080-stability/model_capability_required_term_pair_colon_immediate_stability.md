# MiniGPT Required-Term Pair Colon-Immediate Stability

- Status: `pass`
- Decision: `required_term_pair_colon_immediate_partial_stability`
- Pair-full seeds: `2/3`
- Model quality claim: `targeted_pair_refresh_partial_signal`

## Seeds

| Seed | Status | Pair full | Default full | Suppression full |
| ---: | --- | --- | ---: | ---: |
| 535 | pass | True | 1 | 1 |
| 1535 | pass | False | 0 | 0 |
| 2535 | pass | True | 1 | 1 |

## Boundary

- Reason: Some but not all colon-immediate seeds produced pair-full coverage.
- Next action: inspect missed seeds before increasing corpus or model size

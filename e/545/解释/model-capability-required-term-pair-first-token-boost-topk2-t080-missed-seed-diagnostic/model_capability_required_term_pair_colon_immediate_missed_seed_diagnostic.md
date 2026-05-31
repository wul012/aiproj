# MiniGPT Required-Term Pair Colon-Immediate Missed-Seed Diagnostic

- Status: `pass`
- Decision: `required_term_pair_colon_immediate_first_token_gap`
- Missed seeds: `3`
- Missed expected-top seeds: `0`
- Model quality claim: `targeted_pair_refresh_missed_seed_diagnostic_only`

## Seeds

| Seed | Pair full | First-token decision | Expected top | Fixed rank | Loss rank | Continuation hits |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 535 | False | pair_first_token_expected_terms_not_top_ranked | 1/2 | 2 | 1 | 1 |
| 1535 | False | pair_first_token_expected_terms_not_top_ranked | 1/2 | 2 | 1 | 0 |
| 2535 | False | pair_first_token_expected_terms_not_top_ranked | 0/2 | 2 | 2 | 1 |

## Boundary

- Reason: At least one missed seed does not rank all expected first tokens on top.
- Next action: strengthen first-token preference before extending continuation training

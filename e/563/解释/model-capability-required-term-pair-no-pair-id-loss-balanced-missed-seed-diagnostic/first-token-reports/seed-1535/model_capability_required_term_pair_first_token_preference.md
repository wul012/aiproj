# MiniGPT Required-Term Pair First-Token Preference

- Status: `pass`
- Decision: `pair_first_token_whitespace_prefix_drift_confirmed`
- Expected top count: `1`
- Whitespace-prefix top count: `1`
- Answer-prefix top count: `0`

## Rows

| Term | Prompt | Expected | Rank | Top token | Top prob | Observed continuation |
| --- | --- | --- | ---: | --- | ---: | --- |
| fixed | fixed= | f | 1 | f | 0.32611379 | fixed\nlos= f |
| loss | loss= | l | 3 |   | 0.34261671 |  fixed=loss= |

## Boundary

- Model quality claim: `not_claimed`
- Reason: At least one prompt ranks whitespace above the expected first token, matching the leading-space replay collapse.
- Next action: remove leading-space answer rows or add colon-immediate fixed/loss rows before retraining

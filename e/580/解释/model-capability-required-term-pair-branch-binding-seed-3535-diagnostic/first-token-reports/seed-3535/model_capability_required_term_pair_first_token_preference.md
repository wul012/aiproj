# MiniGPT Required-Term Pair First-Token Preference

- Status: `pass`
- Decision: `pair_first_token_whitespace_prefix_drift_confirmed`
- Expected top count: `0`
- Whitespace-prefix top count: `2`
- Answer-prefix top count: `0`

## Rows

| Term | Prompt | Expected | Rank | Top token | Top prob | Observed continuation |
| --- | --- | --- | ---: | --- | ---: | --- |
| fixed | fixed= | f | 3 |   | 0.70507479 |  losss\nbind= |
| loss | loss= | l | 2 |   | 0.73825479 |  los= fintin |

## Boundary

- Model quality claim: `not_claimed`
- Reason: At least one prompt ranks whitespace above the expected first token, matching the leading-space replay collapse.
- Next action: remove leading-space answer rows or add colon-immediate fixed/loss rows before retraining

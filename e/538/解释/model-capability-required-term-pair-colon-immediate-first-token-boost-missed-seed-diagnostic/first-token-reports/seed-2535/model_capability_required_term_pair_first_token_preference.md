# MiniGPT Required-Term Pair First-Token Preference

- Status: `pass`
- Decision: `pair_first_token_expected_terms_not_top_ranked`
- Expected top count: `1`
- Whitespace-prefix top count: `0`
- Answer-prefix top count: `0`

## Rows

| Term | Prompt | Expected | Rank | Top token | Top prob | Observed continuation |
| --- | --- | --- | ---: | --- | ---: | --- |
| fixed | fixed: | f | 1 | f | 0.31737584 | fixed:lossss |
| loss | loss: | l | 2 | f | 0.32772359 | fixed:lossss |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Expected first tokens are not top ranked, but the dominant token is not the answer prefix.
- Next action: inspect top-token alternatives before changing corpus

# MiniGPT Required-Term Pair First-Token Preference

- Status: `pass`
- Decision: `pair_first_token_expected_terms_not_top_ranked`
- Expected top count: `1`
- Whitespace-prefix top count: `0`
- Answer-prefix top count: `0`

## Rows

| Term | Prompt | Expected | Rank | Top token | Top prob | Observed continuation |
| --- | --- | --- | ---: | --- | ---: | --- |
| fixed | fixed: | f | 1 | f | 0.39648989 | fixed\nfixed\n |
| loss | loss: | l | 2 | f | 0.41908419 | fixed\nfixed\n |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Expected first tokens are not top ranked, but the dominant token is not the answer prefix.
- Next action: inspect top-token alternatives before changing corpus

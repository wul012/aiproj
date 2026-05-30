# MiniGPT Required-Term Pair First-Token Preference

- Status: `pass`
- Decision: `pair_first_token_expected_terms_top_ranked`
- Expected top count: `2`
- Whitespace-prefix top count: `0`
- Answer-prefix top count: `0`

## Rows

| Term | Prompt | Expected | Rank | Top token | Top prob | Observed continuation |
| --- | --- | --- | ---: | --- | ---: | --- |
| fixed | fixed: | f | 1 | f | 0.42091259 | fixed:loss:f |
| loss | loss: | l | 1 | l | 0.48450997 | losssss:fixe |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The expected first tokens are already top ranked, so the failure is likely later in generation.
- Next action: inspect second-token and continuation dynamics

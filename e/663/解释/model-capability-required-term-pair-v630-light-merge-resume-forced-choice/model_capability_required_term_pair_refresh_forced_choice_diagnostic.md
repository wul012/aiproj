# MiniGPT Required-Term Pair Refresh Forced-Choice Diagnostic

- Status: `pass`
- Decision: `refresh_forced_choice_not_recovered`
- Expected-best prompt count: `0`
- Full-match source count: `0`

## Prompt Summaries

| Source | Prompt | Best | Expected best | Expected NLL | Best NLL |
| --- | --- | --- | --- | --- | --- |
| v630-light-merge-resume | fixed | loss | False | 0.664305 | 0.655179 |
| v630-light-merge-resume | loss | fixed | False | 0.688572 | 0.625132 |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Teacher-forced scoring does not prefer the expected terms.
- Next action: change objective shape rather than decoding settings

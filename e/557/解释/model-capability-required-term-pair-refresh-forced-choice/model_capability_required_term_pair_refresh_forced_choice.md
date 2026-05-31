# MiniGPT Required-Term Pair Refresh Forced-Choice

- Status: `pass`
- Decision: `required_term_pair_refresh_forced_choice_preference_collapse`
- Expected-best prompts: `1/2`
- Collapse candidate: `loss`

## Prompt Preference

| Prompt term | Prompt | Expected | Best | Expected best | Margin |
| --- | --- | --- | --- | --- | ---: |
| fixed | fixed= | fixed | loss | False | 0.010357 |
| loss | loss= | loss | loss | True | 0.0 |

## Candidate Scores

| Prompt | Candidate | Expected? | Avg NLL | First rank | Status |
| --- | --- | --- | ---: | ---: | --- |
| fixed= | fixed | True | 0.598999 | 2 | pass |
| fixed= | loss | False | 0.588642 | 1 | pass |
| loss= | fixed | False | 1.015867 | 2 | pass |
| loss= | loss | True | 0.603085 | 1 | pass |

## Boundary

- Model quality claim: `diagnostic_only`
- Reason: Teacher-forced scoring collapses both prompts to loss.
- Next action: avoid more simple corpus weighting and inspect objective/capacity or constrained decoding

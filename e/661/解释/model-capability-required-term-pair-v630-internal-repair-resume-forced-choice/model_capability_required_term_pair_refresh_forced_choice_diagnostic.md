# MiniGPT Required-Term Pair Refresh Forced-Choice Diagnostic

- Status: `pass`
- Decision: `refresh_forced_choice_partial_internal_match`
- Expected-best prompt count: `1`
- Full-match source count: `0`

## Prompt Summaries

| Source | Prompt | Best | Expected best | Expected NLL | Best NLL |
| --- | --- | --- | --- | --- | --- |
| v630-internal-repair-resume | fixed | fixed | True | 0.581696 | 0.581696 |
| v630-internal-repair-resume | loss | fixed | False | 0.647164 | 0.579538 |

## Boundary

- Model quality claim: `partial_internal_signal_only`
- Reason: Some prompts internally prefer the expected term, but no checkpoint matches the pair.
- Next action: use prompt-level internal preference to design the next objective

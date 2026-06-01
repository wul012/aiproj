# MiniGPT Required-Term Pair Refresh Forced-Choice Diagnostic

- Status: `pass`
- Decision: `refresh_forced_choice_partial_internal_match`
- Expected-best prompt count: `3`
- Full-match source count: `0`

## Prompt Summaries

| Source | Prompt | Best | Expected best | Expected NLL | Best NLL |
| --- | --- | --- | --- | --- | --- |
| v611-contrast-free | fixed | fixed | True | 0.402942 | 0.402942 |
| v611-contrast-free | loss | fixed | False | 0.644412 | 0.36692 |
| v612-delimiter-span | fixed | fixed | True | 0.274366 | 0.274366 |
| v612-delimiter-span | loss | fixed | False | 0.548126 | 0.281628 |
| v613-context-switch | fixed | fixed | True | 0.321485 | 0.321485 |
| v613-context-switch | loss | fixed | False | 0.58526 | 0.357116 |

## Boundary

- Model quality claim: `partial_internal_signal_only`
- Reason: Some prompts internally prefer the expected term, but no checkpoint matches the pair.
- Next action: use prompt-level internal preference to design the next objective

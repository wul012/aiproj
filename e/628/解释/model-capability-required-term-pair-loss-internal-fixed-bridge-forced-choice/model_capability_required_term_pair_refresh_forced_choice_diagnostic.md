# MiniGPT Required-Term Pair Refresh Forced-Choice Diagnostic

- Status: `pass`
- Decision: `refresh_forced_choice_partial_internal_match`
- Expected-best prompt count: `1`
- Full-match source count: `0`

## Prompt Summaries

| Source | Prompt | Best | Expected best | Expected NLL | Best NLL |
| --- | --- | --- | --- | --- | --- |
| loss-internal-fixed-bridge | fixed | fixed | True | 0.703207 | 0.703207 |
| loss-internal-fixed-bridge | loss | fixed | False | 0.785461 | 0.722262 |

## Boundary

- Model quality claim: `partial_internal_signal_only`
- Reason: Some prompts internally prefer the expected term, but no checkpoint matches the pair.
- Next action: use prompt-level internal preference to design the next objective

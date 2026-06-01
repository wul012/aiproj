# MiniGPT Required-Term Pair Refresh Forced-Choice Diagnostic

- Status: `pass`
- Decision: `refresh_forced_choice_internal_pair_match`
- Expected-best prompt count: `2`
- Full-match source count: `1`

## Prompt Summaries

| Source | Prompt | Best | Expected best | Expected NLL | Best NLL |
| --- | --- | --- | --- | --- | --- |
| dual-boundary-seed-3535 | fixed | fixed | True | 0.054965 | 0.054965 |
| dual-boundary-seed-3535 | loss | loss | True | 0.123989 | 0.123989 |

## Boundary

- Model quality claim: `forced_choice_internal_signal_only`
- Reason: At least one checkpoint internally prefers the expected term for both prompts.
- Next action: compare internal preference with generation failures before more training

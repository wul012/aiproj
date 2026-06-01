# MiniGPT Required-Term Pair Refresh Forced-Choice Diagnostic

- Status: `pass`
- Decision: `refresh_forced_choice_internal_pair_match`
- Expected-best prompt count: `2`
- Full-match source count: `1`

## Prompt Summaries

| Source | Prompt | Best | Expected best | Expected NLL | Best NLL |
| --- | --- | --- | --- | --- | --- |
| joint-cycle-internal-repair | fixed | fixed | True | 1.015049 | 1.015049 |
| joint-cycle-internal-repair | loss | loss | True | 0.777257 | 0.777257 |

## Boundary

- Model quality claim: `forced_choice_internal_signal_only`
- Reason: At least one checkpoint internally prefers the expected term for both prompts.
- Next action: compare internal preference with generation failures before more training

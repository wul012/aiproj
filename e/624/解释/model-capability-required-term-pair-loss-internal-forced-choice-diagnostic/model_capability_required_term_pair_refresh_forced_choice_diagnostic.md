# MiniGPT Required-Term Pair Refresh Forced-Choice Diagnostic

- Status: `pass`
- Decision: `refresh_forced_choice_internal_pair_match`
- Expected-best prompt count: `4`
- Full-match source count: `1`

## Prompt Summaries

| Source | Prompt | Best | Expected best | Expected NLL | Best NLL |
| --- | --- | --- | --- | --- | --- |
| loss-internal-first-token | fixed | fixed | True | 0.699462 | 0.699462 |
| loss-internal-first-token | loss | loss | True | 0.572295 | 0.572295 |
| loss-internal-preference | fixed | fixed | True | 0.564308 | 0.564308 |
| loss-internal-preference | loss | fixed | False | 0.974691 | 0.5284 |
| loss-internal-ranked-choice | fixed | loss | False | 0.824453 | 0.793944 |
| loss-internal-ranked-choice | loss | loss | True | 0.783144 | 0.783144 |

## Boundary

- Model quality claim: `forced_choice_internal_signal_only`
- Reason: At least one checkpoint internally prefers the expected term for both prompts.
- Next action: compare internal preference with generation failures before more training

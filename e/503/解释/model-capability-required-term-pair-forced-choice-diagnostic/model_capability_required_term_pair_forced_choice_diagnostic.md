# MiniGPT Required-Term Pair Forced-Choice Diagnostic

- Status: `pass`
- Decision: `required_term_pair_forced_choice_internal_match`
- Diagnostic decision: `forced_choice_full_match_observed`
- Source sweep: `branch_retention_sweep_tradeoff_remains`
- Runs: `3`
- Expected-best count: `4`
- Full-match variants: `1`

## Prompt Choices

| Variant | Prompt term | Expected | Best candidate | Expected best | Margin |
| --- | --- | --- | --- | --- | ---: |
| alternating-balanced | fixed | fixed | fixed | True | 0.0 |
| alternating-balanced | loss | loss | fixed | False | 0.546682 |
| symmetric-anchor | fixed | fixed | fixed | True | 0.0 |
| symmetric-anchor | loss | loss | loss | True | 0.0 |
| symmetric-boost | fixed | fixed | fixed | True | 0.0 |
| symmetric-boost | loss | loss | fixed | False | 0.411718 |

## Boundary

- Model quality claim: `forced_choice_internal_signal_only`
- Reason: At least one checkpoint internally preferred the expected term for every pair prompt.
- Next action: compare forced-choice winners with generation decoding to isolate sampling/decoding loss

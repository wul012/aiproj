# MiniGPT Required-Term Pair Coexistence Refresh

- Status: `pass`
- Decision: `required_term_pair_coexistence_refresh_no_pair_full`
- Training status: `pass`
- Pair full observed: `False`
- Model quality claim: `not_claimed`

## Replay Variants

| Variant | Profile | Hit terms | Missed terms | Pair full |
| --- | --- | --- | --- | --- |
| coexistence-refresh | default |  | fixed,loss | False |
| coexistence-refresh | suppress_newline_tokens |  | fixed,loss | False |

## Boundary

- Reason: The refresh run completed but still did not produce full fixed/loss continuation coverage.
- Next action: increase pair objective diversity or inspect first-token preference before more training

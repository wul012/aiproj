# MiniGPT Required-Term Pair Coexistence Refresh

- Status: `pass`
- Decision: `required_term_pair_coexistence_refresh_pair_full_observed`
- Training status: `pass`
- Pair full observed: `True`
- Model quality claim: `targeted_pair_refresh_signal_only`

## Replay Variants

| Variant | Profile | Hit terms | Missed terms | Pair full |
| --- | --- | --- | --- | --- |
| coexistence-refresh | default | loss | fixed | False |
| coexistence-refresh | suppress_newline_tokens | fixed,loss |  | True |

## Boundary

- Reason: A direct fixed/loss refresh corpus produced at least one profile with full pair continuation coverage.
- Next action: repeat the refresh across seeds before promoting it as stable pair coexistence

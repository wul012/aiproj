# MiniGPT Required-Term Pair Generation Profile Replay

- Status: `pass`
- Decision: `generation_profile_partial_pair_surface_only`
- Failed count: `0`
- Suppression hit delta: `1`
- Suppression pair-full delta: `0`

## Profiles

| Profile | Hits | Pair-full variants | Blocked tokens |
| --- | ---: | ---: | ---: |
| default | 0/2 | 0/1 | 0 |
| suppress_newline_tokens | 1/2 | 0/1 | 2 |

## Variants

| Variant | Profile | Hit terms | Missed terms | Pair full |
| --- | --- | --- | --- | --- |
| coexistence-refresh | default |  | fixed,loss | False |
| coexistence-refresh | suppress_newline_tokens | fixed | loss | False |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The suppression profile helped individual continuations but did not create full fixed/loss coexistence.
- Next action: Keep the profile as decode-surface hygiene and continue with pair-training changes.

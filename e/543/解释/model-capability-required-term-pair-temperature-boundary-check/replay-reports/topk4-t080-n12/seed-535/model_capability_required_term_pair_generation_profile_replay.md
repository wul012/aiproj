# MiniGPT Required-Term Pair Generation Profile Replay

- Status: `pass`
- Decision: `generation_profile_improves_pair_coexistence`
- Failed count: `0`
- Suppression hit delta: `1`
- Suppression pair-full delta: `1`

## Profiles

| Profile | Hits | Pair-full variants | Blocked tokens |
| --- | ---: | ---: | ---: |
| default | 1/2 | 0/1 | 0 |
| suppress_newline_tokens | 2/2 | 1/1 | 2 |

## Variants

| Variant | Profile | Hit terms | Missed terms | Pair full |
| --- | --- | --- | --- | --- |
| seed-535 | default | fixed | loss | False |
| seed-535 | suppress_newline_tokens | fixed,loss |  | True |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The suppression profile increased the number of variants where fixed/loss both appear.
- Next action: Promote the profile into the next pair benchmark before retraining.

# MiniGPT Required-Term Pair Generation Profile Replay

- Status: `pass`
- Decision: `generation_profile_no_pair_coexistence_gain`
- Failed count: `0`
- Suppression hit delta: `0`
- Suppression pair-full delta: `0`

## Profiles

| Profile | Hits | Pair-full variants | Blocked tokens |
| --- | ---: | ---: | ---: |
| default | 0/2 | 0/1 | 0 |
| suppress_newline_tokens | 0/2 | 0/1 | 2 |

## Variants

| Variant | Profile | Hit terms | Missed terms | Pair full |
| --- | --- | --- | --- | --- |
| seed-1535 | default |  | fixed,loss | False |
| seed-1535 | suppress_newline_tokens |  | fixed,loss | False |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The suppression profile did not improve fixed/loss continuation hits on archived pair-retention checkpoints.
- Next action: Treat newline suppression as loss-alias cleanup only; the next model-capability step should train for pair coexistence.

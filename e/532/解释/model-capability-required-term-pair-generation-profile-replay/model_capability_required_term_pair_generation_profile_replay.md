# MiniGPT Required-Term Pair Generation Profile Replay

- Status: `pass`
- Decision: `generation_profile_no_pair_coexistence_gain`
- Failed count: `0`
- Suppression hit delta: `0`
- Suppression pair-full delta: `0`

## Profiles

| Profile | Hits | Pair-full variants | Blocked tokens |
| --- | ---: | ---: | ---: |
| default | 2/6 | 0/3 | 0 |
| suppress_newline_tokens | 2/6 | 0/3 | 6 |

## Variants

| Variant | Profile | Hit terms | Missed terms | Pair full |
| --- | --- | --- | --- | --- |
| alternating-balanced | default | fixed | loss | False |
| alternating-balanced | suppress_newline_tokens | fixed | loss | False |
| symmetric-boost | default | fixed | loss | False |
| symmetric-boost | suppress_newline_tokens | fixed | loss | False |
| symmetric-anchor | default |  | fixed,loss | False |
| symmetric-anchor | suppress_newline_tokens |  | fixed,loss | False |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The suppression profile did not improve fixed/loss continuation hits on archived pair-retention checkpoints.
- Next action: Treat newline suppression as loss-alias cleanup only; the next model-capability step should train for pair coexistence.

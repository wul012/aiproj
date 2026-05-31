# MiniGPT Required-Term Pair Generation Profile Replay

- Status: `pass`
- Decision: `generation_profile_no_pair_coexistence_gain`
- Failed count: `0`
- Suppression hit delta: `-1`
- Suppression pair-full delta: `-1`

## Profiles

| Profile | Hits | Pair-full variants | Blocked tokens |
| --- | ---: | ---: | ---: |
| default | 2/2 | 1/1 | 0 |
| suppress_newline_tokens | 1/2 | 0/1 | 2 |

## Variants

| Variant | Profile | Hit terms | Missed terms | Pair full |
| --- | --- | --- | --- | --- |
| heldout-equals-seed-2535 | default | fixed,loss |  | True |
| heldout-equals-seed-2535 | suppress_newline_tokens | loss | fixed | False |

## Boundary

- Model quality claim: `not_claimed`
- Reason: The suppression profile did not improve fixed/loss continuation hits on archived pair-retention checkpoints.
- Next action: Treat newline suppression as loss-alias cleanup only; the next model-capability step should train for pair coexistence.

# MiniGPT Required-Term Pair Loss-Alias Newline Suppression Repeat

- Status: `pass`
- Decision: `required_term_pair_loss_alias_newline_suppression_stable_strict_recovery`
- Repeat decision: `loss_alias_newline_suppression_repeat_stable_strict_recovery`
- Sources: `2/2`
- Baseline full sources: `0`
- Suppressed full sources: `2`
- Strict gains: `8`

## Sources

| Source | Baseline strict | Suppressed strict | Suppressed full | Gains |
| --- | ---: | ---: | --- | ---: |
| v518 | 0 | 4 | True | 4 |
| v523 | 0 | 4 | True | 4 |

## Boundary

- Model quality claim: `tiny_loss_alias_newline_suppression_stable_strict_surface_recovery`
- Reason: Newline-token suppression recovered strict loss hits for every compared focus report while baseline reruns did not.
- Next action: promote newline-suppressed decoding as an experimental evaluation profile and compare it with fresh training

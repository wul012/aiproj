# MiniGPT Required-Term Pair Constrained Decode Feasibility

- Status: `pass`
- Decision: `required_term_pair_constrained_decode_not_feasible`
- Hit delta: `-1`
- Constrained pair-full: `False`

## Profiles

| Profile | Hit terms | Missed terms | Pair full | Blocked tokens |
| --- | --- | --- | --- | ---: |
| block_competing_initial |  | fixed,loss | False | 2 |
| default | loss | fixed | False | 0 |

## Cases

| Profile | Term | Blocked | Hit | Continuation |
| --- | --- | --- | --- | --- |
| default | fixed |  | False | los paross f |
| block_competing_initial | fixed | l | False | 01\npt=01 1 f |
| default | loss |  | True | loss fixes p |
| block_competing_initial | loss | f | False | 01\npaross lo |

## Boundary

- Model quality claim: `decode_feasibility_only`
- Reason: The constraint does not improve fixed/loss continuation hits.
- Next action: return to objective/capacity changes instead of decode-only mitigation

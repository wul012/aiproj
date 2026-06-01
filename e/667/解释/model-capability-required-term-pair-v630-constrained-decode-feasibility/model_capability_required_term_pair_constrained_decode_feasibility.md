# MiniGPT Required-Term Pair Constrained Decode Feasibility

- Status: `pass`
- Decision: `required_term_pair_constrained_decode_partial_gain`
- Hit delta: `1`
- Constrained pair-full: `False`

## Profiles

| Profile | Hit terms | Missed terms | Pair full | Blocked tokens |
| --- | --- | --- | --- | ---: |
| block_competing_initial | loss | fixed | False | 2 |
| default |  | fixed,loss | False | 0 |

## Cases

| Profile | Term | Blocked | Hit | Continuation |
| --- | --- | --- | --- | --- |
| default | fixed |  | False |  d= los\nd=fi |
| block_competing_initial | fixed | l | False |  d= cans\nfix |
| default | loss |  | False |  fixe fixed= |
| block_competing_initial | loss | f | True |  lossssssss= |

## Boundary

- Model quality claim: `decode_feasibility_only`
- Reason: The constraint improves some continuations but does not recover the fixed/loss pair.
- Next action: inspect which term remains missed before promoting a decode profile

# MiniGPT Required-Term Pair Route Held-Out Replay

- Status: `pass`
- Decision: `required_term_pair_route_heldout_replay_ready`
- Selected route: `v562-loss-balanced`
- Held-out pair-full rows: `7/7`
- Held-out all pair-full: `True`

## Replay Rows

| Spec | Seed | Replay full | Default full | Suppression full | Prompts |
| --- | ---: | --- | ---: | ---: | --- |
| colon-spaced | 1535 | True | 1 | 1 | fixed:  / loss:  |
| equals | 1535 | True | 1 | 1 | fixed= / loss= |
| arrow | 1535 | True | 1 | 1 | fixed ->  / loss ->  |
| colon-tight | 1535 | True | 1 | 1 | fixed: / loss: |
| equals-spaced | 1535 | True | 1 | 1 | fixed =  / loss =  |
| value-label | 1535 | True | 1 | 1 | fixed value:  / loss value:  |
| item-label | 1535 | True | 1 | 1 | fixed item:  / loss item:  |

## Boundary

- Model quality claim: `targeted_route_heldout_ready`
- Reason: Every selected route pair-full seed also replayed pair-full coverage across held-out prompt surfaces.
- Next action: test a fresh seed or larger prompt suite before raising the capability claim

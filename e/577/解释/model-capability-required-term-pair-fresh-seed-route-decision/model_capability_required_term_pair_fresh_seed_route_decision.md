# MiniGPT Required-Term Pair Fresh-Seed Route Decision

- Status: `pass`
- Decision: `stop_first_token_and_width_for_fresh_seed`
- Routes: `3`
- Pair-full routes: `0`
- Best residual signal: `v571-loss-balanced`

## Route Rows

| Route | Type | Pair-full | Hit terms | Reasons |
| --- | --- | ---: | --- | --- |
| v571-loss-balanced | baseline | 0/1 | fixed | no_pair_full_seed,loss_term_missing,not_stable |
| v573-first-token | first_token | 0/1 |  | no_pair_full_seed,loss_term_missing,not_stable |
| v575-wider-embd | width_scaling | 0/1 |  | no_pair_full_seed,loss_term_missing,not_stable |

## Boundary

- Model quality claim: `route_decision_only`
- Reason: Compared fresh-seed routes did not reach pair-full and only preserved limited fixed-term evidence.
- Next action: stop first-token rows and width scaling; design a branch-binding objective before another seed sweep

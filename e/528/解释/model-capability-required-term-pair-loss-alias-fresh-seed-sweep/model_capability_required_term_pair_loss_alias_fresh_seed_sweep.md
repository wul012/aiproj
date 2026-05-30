# MiniGPT Required-Term Pair Loss-Alias Fresh Seed Sweep

- Status: `pass`
- Decision: `required_term_pair_loss_alias_fresh_seed_sweep_blocked_token_stably_recovers`
- Seeds: `3`
- Baseline full seeds: `2`
- Blocked-token full seeds: `3`
- Total blocked-token gains: `2`

## Seeds

| Seed | Baseline strict | Blocked strict | Gains | Checkpoint |
| ---: | ---: | ---: | ---: | --- |
| 527 | 4/4 | 4/4 | 0 | True |
| 528 | 2/4 | 4/4 | 2 | True |
| 529 | 4/4 | 4/4 | 0 | True |

## Boundary

- Model quality claim: `fresh_tiny_loss_alias_blocked_token_decode_stably_recovers`
- Reason: Default decoding was not stably strict, but blocked-token decoding recovered every seed.
- Next action: keep blocked-token as an explicit profile and test it in the playground/API surface

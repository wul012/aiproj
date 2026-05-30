# MiniGPT Required-Term Pair Loss-Alias Stability

- Status: `pass`
- Decision: `required_term_pair_loss_alias_stable_partial_hit`
- Stability decision: `loss_alias_stable_partial_hit`
- Seeds: `2/2`
- Full coverage seeds: `1`
- Stable full coverage: `False`

| Seed | Status | Decision | Hit cases | Heldout hits | Full coverage |
| ---: | --- | --- | ---: | ---: | --- |
| 514 | pass | loss_alias_heldout_full_hit | 4 | 3 | True |
| 515 | pass | loss_alias_heldout_partial_hit | 2 | 2 | False |

## Boundary

- Model quality claim: `tiny_loss_alias_seed_stable_partial_signal`
- Reason: Every tested seed recovered at least one held-out loss alias prompt.
- Next action: inspect missed loss alias rows before adding fixed branch back

# MiniGPT Required-Term Pair Loss-Alias Stability

- Status: `pass`
- Decision: `required_term_pair_loss_alias_stable_partial_hit`
- Stability decision: `loss_alias_stable_partial_hit`
- Metric decision: `loss_alias_stable_partial_hit`
- Seeds: `2/2`
- Full coverage seeds: `1`
- Stable full coverage: `False`
- Normalized full coverage seeds: `1`
- Normalization gains: `0`

| Seed | Status | Decision | Strict heldout | Strict full | Norm heldout | Norm full | Gains |
| ---: | --- | --- | ---: | --- | ---: | --- | ---: |
| 514 | pass | loss_alias_heldout_full_hit | 3 | True | 3 | True | 0 |
| 515 | pass | loss_alias_heldout_partial_hit | 2 | False | 2 | False | 0 |

## Boundary

- Model quality claim: `tiny_loss_alias_seed_stable_partial_signal`
- Reason: Every tested seed recovered at least one held-out loss alias prompt.
- Next action: inspect missed loss alias rows before adding fixed branch back

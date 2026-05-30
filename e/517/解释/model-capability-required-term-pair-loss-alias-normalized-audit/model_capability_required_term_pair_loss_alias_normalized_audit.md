# MiniGPT Required-Term Pair Loss-Alias Normalized Audit

- Status: `pass`
- Decision: `required_term_pair_loss_alias_normalized_full_signal`
- Audit decision: `normalized_hidden_full_signal`
- Strict hits: `0/4`
- Normalized hits: `4/4`
- Normalization gains: `4`

| Case | Focus | Strict | Normalized | Gain | Preview |
| --- | --- | --- | --- | --- | --- |
| source-loss | True | False | True | True |  los\ns\ns\ns\ns |
| heldout-beta-loss | True | False | True | True |  los\ns\ns\ns\ns |
| heldout-omega-loss | False | False | True | True |  los\nss\ns\ns\n |
| heldout-theta-loss | False | False | True | True |  los\nss\ns\ns\n |

## Boundary

- Model quality claim: `tiny_loss_alias_normalized_full_signal`
- Reason: Every strict miss becomes a required-term hit after removing formatting separators.
- Next action: add a separate strict-vs-normalized metric before deciding whether to train again

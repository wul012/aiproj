# MiniGPT Required-Term Pair Loss-Alias Decode Cleanup

- Status: `pass`
- Decision: `required_term_pair_loss_alias_remove_newlines_cleanup_recovers_full`
- Cleanup decision: `loss_alias_decode_cleanup_remove_newlines_full`
- Raw hits: `0/4`
- Remove-newlines hits: `4/4`
- Minimal strategy: `remove_newlines`

## Cases

| Case | Raw | Remove newlines | Collapse whitespace | Remove all whitespace | Minimal |
| --- | --- | --- | --- | --- | --- |
| source-loss | False | True | False | True | remove_newlines |
| heldout-beta-loss | False | True | False | True | remove_newlines |
| heldout-omega-loss | False | True | False | True | remove_newlines |
| heldout-theta-loss | False | True | False | True | remove_newlines |

## Boundary

- Model quality claim: `tiny_loss_alias_newline_cleanup_recovers_strict_surface`
- Reason: Removing newline separators would recover strict loss hits for every focused row.
- Next action: test a bounded newline cleanup evaluation before changing the training objective

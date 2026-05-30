# MiniGPT Required-Term Pair Loss-Alias Blocked-Token Fresh Compare

- Status: `pass`
- Decision: `required_term_pair_loss_alias_blocked_token_fresh_strict_recovery`
- Fresh focus decision: `required_term_pair_loss_alias_focus_repaired`
- Fresh focus surface decision: `loss_alias_focus_missed_rows_repaired`
- Blocked-token surface decision: `loss_alias_newline_suppression_strict_full_recovery`
- Baseline strict hits: `10/12`
- Blocked-token strict hits: `12/12`
- Strict gains: `2`

## Cases

| Profile | Case | Source strict | Probe strict | Gain | Preview |
| --- | --- | --- | --- | --- | --- |
| baseline_rerun | source-loss | True | True | False | lossssssssss |
| suppress_newline_tokens | source-loss | True | True | False | lossssssssss |
| baseline_rerun | heldout-beta-loss | True | True | False | lossssssssss |
| suppress_newline_tokens | heldout-beta-loss | True | True | False | lossssssssss |
| baseline_rerun | heldout-omega-loss | True | True | False | lossssssssss |
| suppress_newline_tokens | heldout-omega-loss | True | True | False | lossssssssss |
| baseline_rerun | heldout-theta-loss | True | True | False | lossss losss |
| suppress_newline_tokens | heldout-theta-loss | True | True | False | lossss losss |
| baseline_rerun | source-loss | True | True | False |  loss\nssssss |
| suppress_newline_tokens | source-loss | True | True | False |  losssssssss |
| baseline_rerun | heldout-beta-loss | True | True | False |  loss\nssssss |
| suppress_newline_tokens | heldout-beta-loss | True | True | False |  losssssssss |
| baseline_rerun | heldout-omega-loss | False | False | False |  los\nsssssss |
| suppress_newline_tokens | heldout-omega-loss | False | True | True |  losssssssss |
| baseline_rerun | heldout-theta-loss | False | False | False |  los\nsssssss |
| suppress_newline_tokens | heldout-theta-loss | False | True | True |  losssssssss |
| baseline_rerun | source-loss | True | True | False | lossssssssss |
| suppress_newline_tokens | source-loss | True | True | False | lossssssssss |
| baseline_rerun | heldout-beta-loss | True | True | False | lossssssssss |
| suppress_newline_tokens | heldout-beta-loss | True | True | False | lossssssssss |
| baseline_rerun | heldout-omega-loss | True | True | False | lossssssssss |
| suppress_newline_tokens | heldout-omega-loss | True | True | False | lossssssssss |
| baseline_rerun | heldout-theta-loss | True | True | False | lossssssssss |
| suppress_newline_tokens | heldout-theta-loss | True | True | False | lossssssssss |

## Boundary

- Model quality claim: `fresh_tiny_loss_alias_blocked_token_decoding_recovers_strict_surface`
- Reason: A fresh focused checkpoint still misses strict loss hits with default decoding, while newline-token blocking recovers every probed row.
- Next action: add an explicit generation profile comparison before making blocked tokens a default playground option

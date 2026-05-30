# MiniGPT Required-Term Pair Loss-Alias Blocked-Token Fresh Compare

- Status: `pass`
- Decision: `required_term_pair_loss_alias_blocked_token_fresh_baseline_already_strict`
- Fresh focus decision: `required_term_pair_loss_alias_focus_support_full_hit`
- Fresh focus surface decision: `loss_alias_focus_support_full_hit`
- Blocked-token surface decision: `loss_alias_newline_suppression_baseline_already_full`
- Baseline strict hits: `4/4`
- Blocked-token strict hits: `4/4`
- Strict gains: `0`

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

## Boundary

- Model quality claim: `fresh_tiny_loss_alias_baseline_decode_already_strict`
- Reason: The fresh focused checkpoint already emits strict loss hits without blocked-token decoding.
- Next action: compare this stronger fresh seed against earlier checkpoints before claiming a general training improvement

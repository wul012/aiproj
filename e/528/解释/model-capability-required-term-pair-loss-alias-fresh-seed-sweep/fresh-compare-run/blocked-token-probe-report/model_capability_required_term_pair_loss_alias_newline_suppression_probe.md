# MiniGPT Required-Term Pair Loss-Alias Newline Suppression Probe

- Status: `pass`
- Decision: `required_term_pair_loss_alias_newline_suppression_strict_recovery`
- Suppression decision: `loss_alias_newline_suppression_strict_full_recovery`
- Baseline strict hits: `10/12`
- Suppressed strict hits: `12/12`
- Strict gains: `2`

## Profiles

| Profile | Strict hits | Strict full | Focus hits | Focus full | Gains |
| --- | ---: | --- | ---: | --- | ---: |
| baseline_rerun | 10 | False | 6 | True | 0 |
| suppress_newline_tokens | 12 | True | 6 | True | 2 |

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

- Model quality claim: `tiny_loss_alias_decoding_newline_suppression_recovers_strict_surface`
- Reason: Masking newline tokens during decoding recovers strict loss hits for every probed loss-alias row.
- Next action: compare newline-suppressed decoding against a fresh training run before changing the corpus

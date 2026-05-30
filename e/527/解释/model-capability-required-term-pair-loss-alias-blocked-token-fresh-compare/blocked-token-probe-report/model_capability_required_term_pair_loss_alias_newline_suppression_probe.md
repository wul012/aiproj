# MiniGPT Required-Term Pair Loss-Alias Newline Suppression Probe

- Status: `pass`
- Decision: `required_term_pair_loss_alias_newline_suppression_strict_recovery`
- Suppression decision: `loss_alias_newline_suppression_baseline_already_full`
- Baseline strict hits: `4/4`
- Suppressed strict hits: `4/4`
- Strict gains: `0`

## Profiles

| Profile | Strict hits | Strict full | Focus hits | Focus full | Gains |
| --- | ---: | --- | ---: | --- | ---: |
| baseline_rerun | 4 | True | 2 | True | 0 |
| suppress_newline_tokens | 4 | True | 2 | True | 0 |

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

- Model quality claim: `tiny_loss_alias_decoding_newline_suppression_recovers_strict_surface`
- Reason: Masking newline tokens during decoding recovers strict loss hits for every probed loss-alias row.
- Next action: compare newline-suppressed decoding against a fresh training run before changing the corpus

# MiniGPT Required-Term Pair Loss-Alias Newline Suppression Probe

- Status: `pass`
- Decision: `required_term_pair_loss_alias_newline_suppression_strict_recovery`
- Suppression decision: `loss_alias_newline_suppression_strict_full_recovery`
- Baseline strict hits: `0/4`
- Suppressed strict hits: `4/4`
- Strict gains: `4`

## Profiles

| Profile | Strict hits | Strict full | Focus hits | Focus full | Gains |
| --- | ---: | --- | ---: | --- | ---: |
| baseline_rerun | 0 | False | 0 | False | 0 |
| suppress_newline_tokens | 4 | True | 2 | True | 4 |

## Cases

| Profile | Case | Source strict | Probe strict | Gain | Preview |
| --- | --- | --- | --- | --- | --- |
| baseline_rerun | source-loss | False | False | False |  los\ns\ns\ns\ns |
| suppress_newline_tokens | source-loss | False | True | True |  losssssssss |
| baseline_rerun | heldout-beta-loss | False | False | False |  los\ns\ns\ns\ns |
| suppress_newline_tokens | heldout-beta-loss | False | True | True |  losssssssss |
| baseline_rerun | heldout-omega-loss | False | False | False |  los\nss\ns\ns\n |
| suppress_newline_tokens | heldout-omega-loss | False | True | True |  losssssssss |
| baseline_rerun | heldout-theta-loss | False | False | False |  los\nss\ns\ns\n |
| suppress_newline_tokens | heldout-theta-loss | False | True | True |  losssssssss |

## Boundary

- Model quality claim: `tiny_loss_alias_decoding_newline_suppression_recovers_strict_surface`
- Reason: Masking newline tokens during decoding recovers strict loss hits for every probed loss-alias row.
- Next action: compare newline-suppressed decoding against a fresh training run before changing the corpus

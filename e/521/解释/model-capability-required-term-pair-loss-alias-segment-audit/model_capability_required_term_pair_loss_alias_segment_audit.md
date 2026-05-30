# MiniGPT Required-Term Pair Loss-Alias Segment Audit

- Status: `pass`
- Decision: `required_term_pair_loss_alias_newline_segment_boundary`
- Segment decision: `loss_alias_segment_newline_split`
- Normalization gains: `4`
- Dominant separator: `newline`
- Tokenizers loaded: `4`

## Cases

| Case | Strict | Normalized | Gain | Separator | Tokens | Continuation |
| --- | --- | --- | --- | --- | ---: | --- |
| source-loss | False | True | True | newline | 12 |  los\ns\ns\ns\ns |
| heldout-beta-loss | False | True | True | newline | 12 |  los\ns\ns\ns\ns |
| heldout-omega-loss | False | True | True | newline | 12 |  los\nss\ns\ns\n |
| heldout-theta-loss | False | True | True | newline | 12 |  los\nss\ns\ns\n |

## Boundary

- Model quality claim: `tiny_loss_alias_formatting_boundary_observed`
- Reason: All normalization gains came from loss characters split by newline separators.
- Next action: test decoding cleanup or stop-token handling before changing the training corpus again

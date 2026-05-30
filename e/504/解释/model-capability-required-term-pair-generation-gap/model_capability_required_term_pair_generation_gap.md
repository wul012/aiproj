# MiniGPT Required-Term Pair Generation Gap

- Status: `pass`
- Decision: `required_term_pair_generation_gap_observed`
- Gap decision: `generation_gap_internal_signal_not_expressed`
- Internal-only prompts: `2`
- Forced-generation gap variants: `1`
- Best gap variant: `symmetric-anchor`

## Gap Rows

| Variant | Prompt | Forced best | Generation hit | Gap class | Continuation |
| --- | --- | --- | --- | --- | --- |
| alternating-balanced | fixed | fixed | True | aligned_hit |  fixed\nfixed |
| alternating-balanced | loss | fixed | False | aligned_miss |  fixed\nfixed |
| symmetric-anchor | fixed | fixed | False | internal_only | didddf\nf\nfix |
| symmetric-anchor | loss | loss | False | internal_only | ssssssssssss |
| symmetric-boost | fixed | fixed | True | aligned_hit |  fixed\nfixed |
| symmetric-boost | loss | fixed | False | aligned_miss |  fixed\nfixed |

## Boundary

- Model quality claim: `internal_signal_not_free_generation_quality`
- Reason: At least one checkpoint has a forced-choice full match that is not expressed by archived free generation.
- Next action: probe deterministic decoding around the best gap variant before changing corpus weights again

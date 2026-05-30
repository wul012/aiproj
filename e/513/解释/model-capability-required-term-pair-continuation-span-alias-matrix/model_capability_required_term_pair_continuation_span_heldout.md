# MiniGPT Required-Term Pair Continuation-Span Heldout

- Status: `pass`
- Decision: `required_term_pair_continuation_span_heldout_signal`
- Heldout decision: `heldout_prompt_generalization_observed`
- Source hit cases: `1/2`
- Heldout hit cases: `3/6`
- Heldout hit terms: `1/2`
- Heldout full term coverage: `False`

| Seed | Case | Type | Expected | Hit | Preview |
| ---: | --- | --- | --- | --- | --- |
| 510 | source-fixed | source | fixed | True | \npan fixed:\n |
| 510 | source-loss | source | loss | False | \npan fixed:\n |
| 510 | heldout-alpha-fixed | heldout | fixed | True | \npan fixed:\n |
| 510 | heldout-gamma-fixed | heldout | fixed | True | \npan fixed:\n |
| 510 | heldout-delta-fixed | heldout | fixed | True | \npan fixed:\n |
| 510 | heldout-beta-loss | heldout | loss | False | \npan fixed:\n |
| 510 | heldout-theta-loss | heldout | loss | False | \npan fixed:\n |
| 510 | heldout-omega-loss | heldout | loss | False | \npan fixed:\n |
| 511 | source-fixed | source | fixed | True | \npafin fixed |
| 511 | source-loss | source | loss | False | \npafixed fix |
| 511 | heldout-alpha-fixed | heldout | fixed | True | \npafin fixed |
| 511 | heldout-gamma-fixed | heldout | fixed | True | \npafin fixed |
| 511 | heldout-delta-fixed | heldout | fixed | True | \npafin fixed |
| 511 | heldout-beta-loss | heldout | loss | False | \npafixed fix |
| 511 | heldout-theta-loss | heldout | loss | False | \npafin fixed |
| 511 | heldout-omega-loss | heldout | loss | False | \npafin fixed |

## Boundary

- Model quality claim: `tiny_continuation_span_heldout_signal`
- Reason: At least one held-out alias prompt emitted its expected required term.
- Next action: repeat held-out prompts across more aliases before promoting the signal

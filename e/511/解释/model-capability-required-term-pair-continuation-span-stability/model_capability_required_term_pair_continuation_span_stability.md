# MiniGPT Required-Term Pair Continuation-Span Stability

- Status: `pass`
- Decision: `required_term_pair_continuation_span_prefix_gain_stable`
- Stability decision: `continuation_span_prefix_gain_stable`
- Seeds: `2/2`
- Prefix gain seeds: `2`
- Stable prefix gain: `True`

| Seed | Status | Decision | Prefix gains | One-token hits | Full generation |
| ---: | --- | --- | ---: | ---: | --- |
| 510 | pass | required_term_pair_continuation_span_prefix_gain | 1 | 2 | False |
| 511 | pass | required_term_pair_continuation_span_prefix_gain | 1 | 2 | False |

## Boundary

- Model quality claim: `tiny_continuation_span_prefix_stability_signal`
- Reason: Every seed improved the source prefix-completion minimum for at least one target.
- Next action: add held-out prompt variants to test whether the stable prefix gain generalizes beyond copied scaffolds

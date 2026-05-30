# MiniGPT Required-Term Pair Continuation-Span Objective

- Status: `pass`
- Decision: `required_term_pair_continuation_span_prefix_gain`
- Span decision: `continuation_span_prefix_minimum_improved`
- Training status: `pass`
- Checkpoint: `e\510\解释\model-capability-required-term-pair-continuation-span-objective\continuation-span-run\checkpoint.pt`
- Generation hits: `0`
- Prefix improvements: `1`

## Prefix Comparison

| Term | Source min prefix | Candidate min prefix | Delta | Candidate one-token |
| --- | ---: | ---: | ---: | --- |
| fixed | 4 | 1 | -3 | True |
| loss | 1 | 1 | 0 | True |

## Free Generation Probes

| Term | Continuation hit | Preview |
| --- | --- | --- |
| fixed | False | \npan losssss |
| loss | False | \nsssssssssss |

## Boundary

- Model quality claim: `tiny_continuation_span_prefix_signal`
- Reason: The tiny continuation-span run reduced the forced-prefix length needed for at least one target term.
- Next action: evaluate whether the prefix gain survives a second seed and a held-out prompt

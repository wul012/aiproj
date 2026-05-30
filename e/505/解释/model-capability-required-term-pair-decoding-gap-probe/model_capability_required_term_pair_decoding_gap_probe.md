# MiniGPT Required-Term Pair Decoding Gap Probe

- Status: `pass`
- Decision: `required_term_pair_decoding_gap_partial_only`
- Probe decision: `decoding_gap_probe_partial_expression_only`
- Continuation hits: `2`
- Full-hit profiles: `0`
- Best profile: `top2-24`

## Probe Rows

| Variant | Profile | Prompt | Hit | Continuation |
| --- | --- | --- | --- | --- |
| symmetric-anchor | greedy-12 | fixed | False | didddf f fix |
| symmetric-anchor | greedy-12 | loss | False | ssssssssssss |
| symmetric-anchor | greedy-24 | fixed | True | didddf f fixedddddddd:lo |
| symmetric-anchor | greedy-24 | loss | False | ssssssssssssssssssssssss |
| symmetric-anchor | top2-24 | fixed | False | didddf:losssssssssssssss |
| symmetric-anchor | top2-24 | loss | True | sssssss lossssssssssssss |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Some decoding probes expressed expected terms, but no profile expressed the full pair.
- Next action: inspect first-token rank and sampled path before adding more training variants

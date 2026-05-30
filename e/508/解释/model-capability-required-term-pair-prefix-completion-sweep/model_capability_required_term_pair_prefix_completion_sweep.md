# MiniGPT Required-Term Pair Prefix Completion Sweep

- Status: `pass`
- Decision: `required_term_pair_prefix_completion_long_prefix`
- Sweep decision: `prefix_completion_requires_longer_prefix`
- One-token hits: `3`
- Full-prefix hits: `6`

## Probe Summaries

| Profile | Prompt | Tokens | Min hit prefix | One-token hit | Full-prefix hit | Preview |
| --- | --- | ---: | ---: | --- | --- | --- |
| greedy-12 | fixed | 5 | 4 | False | True | fixedfeddddd |
| greedy-12 | loss | 4 | 1 | True | True | lossssssssss |
| greedy-24 | fixed | 5 | 4 | False | True | fixedfedddddddd:lossssss |
| greedy-24 | loss | 4 | 1 | True | True | lossssssssssssssssssssss |
| top2-24 | fixed | 5 | 4 | False | True | fixedloddddd lossss f-ss |
| top2-24 | loss | 4 | 1 | True | True | losssssss fixssss lossss |

## Boundary

- Model quality claim: `forced_prefix_completion_signal`
- Reason: All probes retain the expected term with a full prefix, but some require longer forced prefixes.
- Next action: compare prefix completion with a tiny continuation-span objective before more decoding tweaks

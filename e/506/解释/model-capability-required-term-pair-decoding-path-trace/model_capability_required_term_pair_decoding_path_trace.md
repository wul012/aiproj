# MiniGPT Required-Term Pair Decoding Path Trace

- Status: `pass`
- Decision: `required_term_pair_decoding_path_late_expression`
- Trace decision: `decoding_path_trace_late_expression_after_first_miss`
- First-token matches: `0`
- Late hits: `2`

## Probe Summaries

| Profile | Prompt | Hit | First rank | First sample | Late hit | Seen step | Continuation |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| greedy-12 | fixed | False | 2 | d | False | 5 | didddf f fix |
| greedy-12 | loss | False | 2 | s | False |  | ssssssssssss |
| greedy-24 | fixed | True | 2 | d | True | 5 | didddf f fixedddddddd:lo |
| greedy-24 | loss | False | 2 | s | False |  | ssssssssssssssssssssssss |
| top2-24 | fixed | False | 3 | d | False | 5 | didddf:losssssssssssssss |
| top2-24 | loss | True | 3 | s | True | 8 | sssssss lossssssssssssss |

## Boundary

- Model quality claim: `late_generation_expression_only`
- Reason: Some expected terms appear only after the first sampled token already missed the expected first token.
- Next action: test constrained first-token repair before changing training data

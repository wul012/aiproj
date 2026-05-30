# MiniGPT Required-Term Pair First-Token Repair

- Status: `pass`
- Decision: `required_term_pair_first_token_repair_improved_partial`
- Repair decision: `first_token_repair_improved_partial_expression`
- Improved prompts: `2`
- Full-hit profiles: `0`

## Repair Rows

| Profile | Prompt | Source hit | Repaired hit | Forced first | Repaired continuation |
| --- | --- | --- | --- | --- | --- |
| greedy-12 | fixed | False | False | f | fidddfix fix |
| greedy-12 | loss | False | True | l | lossssssssss |
| greedy-24 | fixed | True | False | f | fidddfix fixxedddddddd:l |
| greedy-24 | loss | False | True | l | lossssssssssssssssssssss |
| top2-24 | fixed | False | False | f | fidddfix losssssssssssss |
| top2-24 | loss | True | True | l | l-lossss losssssssssssss |

## Boundary

- Model quality claim: `constrained_generation_partial_signal`
- Reason: Forcing the expected first token improves at least one previously missed prompt.
- Next action: treat the issue as deeper continuation modeling rather than only first-token sampling

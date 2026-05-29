# MiniGPT Model Capability Required-Term One-Term Isolation

- Status: `pass`
- Decision: `required_term_one_term_capacity_observed`
- One-term decision: `one_term_isolation_capacity_observed`
- Terms: `9`
- Training pass count: `9`
- Checkpoints: `9`
- Continuation hits: `5`
- Terms with hits: `5`
- Previous continuation hits: `0`
- Continuation hit delta: `5`

| Term | Prompt | Training | Checkpoint | Continuation hit | Preview |
| --- | --- | --- | --- | ---: | --- |
| because | because: | pass | True | 0 |   b ecauseca |
| fixed | fixed: | pass | True | 1 | fixed:fixed: |
| text | text: | pass | True | 1 | textetextext |
| loss | loss: | pass | True | 1 |  ss\nlossss\nl |
| data | data: | pass | True | 0 |  a: a: da: a |
| real | real: | pass | True | 0 | ral\nreaalrea |
| four | four: | pass | True | 1 | four:four:fo |
| while | while: | pass | True | 0 | wwwile::wwwh |
| chain | chain: | pass | True | 1 |  chn: chain: |

## Boundary

- Model quality claim: `one_term_capacity_signal_only`
- Reason: At least one one-term checkpoint emitted its required term in continuation, isolating single-target capacity.
- Next action: repeat successful one-term cases across seeds before returning to multi-term training

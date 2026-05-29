# MiniGPT Model Capability Required-Term Pair Curriculum

- Status: `pass`
- Decision: `required_term_pair_curriculum_partial`
- Pair decision: `pair_curriculum_partial_only`
- Source stable terms: `4`
- Selected terms: `4`
- Pairs: `6`
- Training pass count: `6`
- Checkpoints: `6`
- Probe hits: `6`
- Full-hit pairs: `0`
- Partial pairs: `6`

| Pair | Hit terms | Missed terms | Hit rate | Full hit |
| --- | --- | --- | ---: | --- |
| fixed, loss | fixed | loss | 0.5 | False |
| fixed, four | four | fixed | 0.5 | False |
| fixed, chain | fixed | chain | 0.5 | False |
| loss, four | loss | four | 0.5 | False |
| loss, chain | chain | loss | 0.5 | False |
| four, chain | chain | four | 0.5 | False |

## Boundary

- Model quality claim: `pair_curriculum_partial_signal_only`
- Reason: Some probes hit their required term, but no pair preserved both targets together.
- Next action: inspect partially successful pairs and rebalance pair corpus before adding more targets

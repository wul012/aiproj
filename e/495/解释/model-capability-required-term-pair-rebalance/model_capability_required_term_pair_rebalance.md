# MiniGPT Model Capability Required-Term Pair Rebalance

- Status: `pass`
- Decision: `required_term_pair_rebalance_capacity_gain`
- Rebalance decision: `pair_rebalance_full_hit_gain`
- Source pair decision: `pair_curriculum_partial_only`
- Selected pairs: `6`
- Training pass count: `6`
- Checkpoints: `6`
- Probe hits: `5`
- Probe hit delta: `-1`
- Full-hit pairs: `1`
- Full-hit delta: `1`

| Pair | Source hits | Rebalance hits | Delta | Full after |
| --- | --- | --- | ---: | --- |
| fixed, loss | fixed | fixed, loss | 1 | True |
| fixed, four | four | four | 0 | False |
| fixed, chain | fixed | chain | 0 | False |
| loss, four | loss | four | 0 | False |
| loss, chain | chain |  | -1 | False |
| four, chain | chain |  | -1 | False |

## Boundary

- Model quality claim: `pair_rebalance_capacity_signal_only`
- Reason: At least one previously partial pair emitted both required terms after rebalance training.
- Next action: repeat the improved pairs across seeds before attempting three-term curricula

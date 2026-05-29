# MiniGPT Model Capability Token Budget Probe

- Status: `pass`
- Decision: `token_budget_probe_ready`
- Summary decision: `longer_token_budget_reduces_eval_stall`
- Baseline token cap: `4`
- Largest token cap: `12`
- Token stall delta: `-9.0`
- Score improved delta: `0.0`
- Pass transition delta: `0.0`
- Persistent fail delta: `-9.0`

| Token cap | Status | Token stalls | Score improved | Pass transitions | Avg score delta | Decision |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 4 | pass | 10 | 0 | 0 | 0.0 | token_budget_or_shape_limits_block_eval_signal |
| 12 | pass | 1 | 0 | 0 | 0.0 | token_budget_or_shape_limits_block_eval_signal |

## Boundary

- Model quality claim: `not_claimed`
- Reason: A longer token budget reduced at least one prompt-level stall signal, but this remains tiny smoke evidence.
- Next action: repeat the longer-token probe across seeds before increasing model size

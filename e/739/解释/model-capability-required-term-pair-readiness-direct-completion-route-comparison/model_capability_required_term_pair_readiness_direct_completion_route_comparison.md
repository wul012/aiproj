# MiniGPT Pair-Readiness Direct-Completion Route Comparison

- Status: `pass`
- Decision: `pair_readiness_direct_completion_route_candidate_found`

## Routes

| Route | Hits | Pair-full | Missed | Loss->fixed | Fixed->loss | Non-term |
| --- | --- | --- | --- | --- | --- | --- |
| objective-structure | 0 | False | ['fixed', 'loss'] | 0 | 0 | 2 |
| direct-prompt-bridge | 0 | False | ['fixed', 'loss'] | 1 | 0 | 1 |
| direct-completion-surface | 2 | True | [] | 0 | 0 | 0 |

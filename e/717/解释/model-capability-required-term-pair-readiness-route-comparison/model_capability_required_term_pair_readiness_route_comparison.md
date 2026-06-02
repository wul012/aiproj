# MiniGPT Pair-Readiness Route Comparison

- Status: `pass`
- Decision: `pair_readiness_structured_template_changes_failure_shape_without_pair_full`

| Route | Pair-full | Default hits | Hit terms | Missed terms | Claim |
| --- | --- | --- | --- | --- | --- |
| baseline-split | False | 1 | ['fixed'] | ['loss'] | not_claimed |
| loss-retention-prefix | False | 0 | [] | ['fixed', 'loss'] | not_claimed |
| structured-template | False | 1 | ['loss'] | ['fixed'] | not_claimed |

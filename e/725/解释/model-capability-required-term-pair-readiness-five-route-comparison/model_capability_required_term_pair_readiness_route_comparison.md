# MiniGPT Pair-Readiness Route Comparison

- Status: `pass`
- Decision: `pair_readiness_capacity_probe_no_improvement_fixed_only`

| Route | Pair-full | Default hits | Hit terms | Missed terms | Claim |
| --- | --- | --- | --- | --- | --- |
| baseline-split | False | 1 | ['fixed'] | ['loss'] | not_claimed |
| loss-retention-prefix | False | 0 | [] | ['fixed', 'loss'] | not_claimed |
| structured-template | False | 1 | ['loss'] | ['fixed'] | not_claimed |
| fixed-recovery | False | 1 | ['fixed'] | ['loss'] | not_claimed |
| capacity-probe | False | 1 | ['fixed'] | ['loss'] | not_claimed |

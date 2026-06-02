# MiniGPT Pair-Readiness Route Comparison

- Status: `pass`
- Decision: `pair_readiness_fixed_recovery_returns_to_baseline_without_pair_full`

| Route | Pair-full | Default hits | Hit terms | Missed terms | Claim |
| --- | --- | --- | --- | --- | --- |
| baseline-split | False | 1 | ['fixed'] | ['loss'] | not_claimed |
| loss-retention-prefix | False | 0 | [] | ['fixed', 'loss'] | not_claimed |
| structured-template | False | 1 | ['loss'] | ['fixed'] | not_claimed |
| fixed-recovery | False | 1 | ['fixed'] | ['loss'] | not_claimed |

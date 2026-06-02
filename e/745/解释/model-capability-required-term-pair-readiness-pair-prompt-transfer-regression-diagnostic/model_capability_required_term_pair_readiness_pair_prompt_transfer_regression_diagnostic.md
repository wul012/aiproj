# MiniGPT Pair Prompt Transfer Regression Diagnostic

- Status: `pass`
- Decision: `pair_readiness_pair_prompt_transfer_regressed_stop_route`

## Evidence Rows

| Evidence | Kind | Hits | Pair-full | Missed | Decision |
| --- | --- | --- | --- | --- | --- |
| direct-completion-surface | training | ['fixed', 'loss'] | True | [] | pair_readiness_training_pair_full_observed |
| direct-completion-pair-probe | pair_probe_replay | [] | False | [] | pair_readiness_direct_completion_pair_probe_replay_not_ready |
| pair-prompt-transfer | training | ['loss'] | False | ['fixed'] | pair_readiness_training_no_pair_full |

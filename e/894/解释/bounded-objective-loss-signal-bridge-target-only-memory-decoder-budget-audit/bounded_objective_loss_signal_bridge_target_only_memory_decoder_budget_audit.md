# MiniGPT bounded objective loss signal bridge target-only memory decoder budget audit

- Status: `pass`
- Decision: `bounded_objective_loss_signal_bridge_target_only_memory_decoder_budget_exhausted_before_loss_suffix`
- Budget exhausted cases: `3`
- Loss suffix top-1 cases: `3`
- Recommended max new tokens: `11`
- Max additional tokens needed: `3`
- Next step: `rerun_stagnation_aware_suffix_replay_with_max_new_tokens_11`

## Case Budget Rows

| Case | Continuation tokens | Max new | Remaining | Suffix | Suffix tokens | Needed max | State |
| --- | --- | --- | --- | --- | --- | --- | --- |
| canonical_direct_completion | 8 | 8 | 0 | oss | 3 | 11 | budget_exhausted_before_top1_suffix |
| minimal_direct_completion | 8 | 8 | 0 | oss | 3 | 11 | budget_exhausted_before_top1_suffix |
| completion_label_surface | 8 | 8 | 0 | oss | 3 | 11 | budget_exhausted_before_top1_suffix |

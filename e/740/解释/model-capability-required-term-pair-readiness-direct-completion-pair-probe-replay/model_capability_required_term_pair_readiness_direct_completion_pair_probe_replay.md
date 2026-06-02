# MiniGPT Pair-Readiness Direct-Completion Pair-Probe Replay

- Status: `pass`
- Decision: `pair_readiness_direct_completion_pair_probe_replay_not_ready`
- Selected training report: `e\738\解释\model-capability-required-term-pair-readiness-direct-completion-surface-training-run\model_capability_required_term_pair_readiness_training_run.json`

## Replay Rows

| Spec | Prompt | Required | Pair-full | Default full | Suppression full |
| --- | --- | --- | --- | ---: | ---: |
| exact-heldout-pair | fixed=\|loss= | True | False | 0 | 0 |
| spaced-heldout-pair | fixed= \| loss= | False | False | 0 | 0 |
| arrow-heldout-pair | fixed -> \| loss -> | False | False | 0 | 0 |

# MiniGPT Fixed-Preserving Transfer Pair-Probe Replay

- Status: `pass`
- Decision: `pair_readiness_fixed_preserving_transfer_pair_probe_replay_ready`
- Training decision: `pair_readiness_training_pair_full_observed`

## Replay Rows

| Spec | Prompt | Required | Replay full | Default hits | Suppression hits |
| --- | --- | --- | --- | --- | --- |
| exact-heldout-pair | fixed=\|loss= | True | True | 2 | 2 |
| spaced-heldout-pair | fixed= \| loss= | False | True | 2 | 2 |
| arrow-heldout-pair | fixed -> \| loss -> | False | False | 1 | 1 |

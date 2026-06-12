# MiniGPT unassisted holdout repair training run v1150

- Generated: `2026-06-12T13:40:14Z`
- Status: `pass`
- Decision: `unassisted_holdout_repair_training_run_ready`

## Summary

| Metric | Value |
| --- | --- |
| unassisted_holdout_repair_training_ready | True |
| artifact_count | 9 |
| metric_record_count | 6 |
| final_step | 50 |
| final_train_loss | 1.2284066677093506 |
| final_val_loss | 1.499302864074707 |
| train_loss_delta | -1.802382 |
| val_loss_delta | -1.49502 |
| sample_fixed_hit | True |
| sample_loss_hit | False |
| model_quality_claim | training_artifact_only |
| promotion_ready | False |
| proposed_next_artifact | unassisted_holdout_repair_replay_comparison_v1151 |
| next_step | run_unassisted_holdout_repair_replay_comparison |
| failed_check_count | 0 |

## Training Artifacts

| key | path | exists | size |
| --- | --- | --- | --- |
| checkpoint | output\unassisted-holdout-repair-training-run-v1150\run\checkpoint.pt | True | 70690 |
| tokenizer | output\unassisted-holdout-repair-training-run-v1150\run\tokenizer.json | True | 290 |
| metrics | output\unassisted-holdout-repair-training-run-v1150\run\metrics.jsonl | True | 673 |
| train_config | output\unassisted-holdout-repair-training-run-v1150\run\train_config.json | True | 983 |
| run_manifest | output\unassisted-holdout-repair-training-run-v1150\run\run_manifest.json | True | 10895 |
| history_summary | output\unassisted-holdout-repair-training-run-v1150\run\history_summary.json | True | 209 |
| loss_curve | output\unassisted-holdout-repair-training-run-v1150\run\loss_curve.svg | True | 1425 |
| sample | output\unassisted-holdout-repair-training-run-v1150\run\sample.txt | True | 90 |
| prepared_corpus | output\unassisted-holdout-repair-training-run-v1150\run\prepared_corpus.txt | True | 216 |

# MiniGPT unassisted holdout repair plan v1148

- Generated: `2026-06-12T12:45:17Z`
- Status: `pass`
- Decision: `unassisted_holdout_repair_plan_ready`

## Summary

| Metric | Value |
| --- | --- |
| unassisted_holdout_repair_plan_ready | True |
| route | unassisted_holdout_repair |
| work_item_count | 6 |
| acceptance_gate_count | 5 |
| blocked_action_count | 4 |
| seed_blueprint_count | 9 |
| new_training_allowed | True |
| promotion_ready | False |
| model_quality_claim | plan_only |
| proposed_next_artifact | unassisted_holdout_repair_seed_corpus_v1149 |
| next_step | materialize_unassisted_holdout_repair_seed_corpus |
| failed_check_count | 0 |

## Repair Work Items

| id | priority | stage | description | expected_output |
| --- | --- | --- | --- | --- |
| materialize_unassisted_seed_blueprint | high | seed | Write a compact seed corpus whose prompts do not contain fixed/loss but completions require the pair. | unassisted_holdout_repair_seed_corpus |
| recover_fixed_first_token | high | training | Bias the next repair run toward generating fixed as new text, because v1147 had zero unassisted fixed hits. | fixed_first_token_uptake_report |
| preserve_loss_suffix_signal | medium | training | Keep the partial loss signal observed in v1147 while adding fixed/loss coexistence examples. | loss_suffix_retention_report |
| run_bounded_repair_checkpoint | high | execution | Train one small CPU repair checkpoint from the unassisted seed blueprint without changing the evaluation prompts. | unassisted_holdout_repair_training_run |
| replay_unchanged_unassisted_prompts | high | evaluation | Rerun the exact five v1147 unassisted prompts and require fixed/loss pair recovery before any stronger claim. | unassisted_holdout_repair_replay |
| compare_against_anchor_baseline | medium | evaluation | Compare repaired unassisted pair hits against the v1147 anchor-assisted baseline and keep promotion gated. | anchor_vs_unassisted_repair_delta |

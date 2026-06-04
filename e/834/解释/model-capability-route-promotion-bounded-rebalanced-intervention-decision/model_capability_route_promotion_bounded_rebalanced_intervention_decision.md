# MiniGPT model capability route promotion bounded rebalanced intervention decision

- Status: `pass`
- Decision: `stop_rebalanced_decoder_rescue_and_design_objective_contract_intervention`
- Selected intervention: `objective_contract_intervention_first`
- Recommended next artifact: `model_capability_route_promotion_bounded_objective_intervention_plan`
- Model-quality claim: `route_decision_only`

## Route

| Field | Value |
| --- | --- |
| closed_route | decoder_anchor_rebalanced_rescue |
| evidence_window | v829-v833 |
| selected_intervention_track | objective_contract_intervention_first |
| fallback_intervention_track | architecture_capacity_probe_if_objective_contract_fails |
| promotion_allowed | False |
| new_training_allowed | False |

## Evidence

| Stage | Status | Signal | Values |
| --- | --- | --- | --- |
| rebalanced_seed_revision | pass | direct/carry distribution repaired | {'direct_answer_share': 0.375, 'carry_forward_share': 0.25} |
| rebalanced_training_run | pass | real checkpoint was trained from the rebalanced corpus | {'final_val_loss': 4.194498062133789} |
| checkpoint_comparison | pass | rebalanced checkpoint did not beat baseline or recover promotion | {'delta_baseline': -0.4, 'passed': 0} |
| failure_diagnostic | pass | all replay cases remained zero-hit after rebalancing | {'zero_hit_case_count': 5, 'fragment_like_case_count': 5} |
| profile_sweep | pass | decoder profile sweep did not recover required terms | {'best_profile_id': 'greedy_short', 'best_passed_case_count': 0, 'best_any_hit_case_count': 0} |

## Stop Reasons

- `distribution_repaired`
- `rebalanced_replay_zero_hit`
- `decoder_profile_sweep_no_recovery`
- `no_required_term_hit_across_profiles`

## Blocked Actions

- `do_not_continue_decoder_profile_rescue`
- `do_not_add_more_rebalanced_training_epochs_without_new_objective`
- `do_not_claim_model_quality_improvement`

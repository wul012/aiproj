# MiniGPT Model Capability Honest Measurement Gate

- Generated: `2026-07-07T04:30:59Z`
- Status: `pass`
- Decision: `continue_with_honest_measurement_gate`
- Registry: `docs/model-capability-honest-measurement-registry.json`

## Summary

| Metric | Value |
| --- | --- |
| family_count | 2 |
| check_count | 68 |
| passed_check_count | 68 |
| failed_check_count | 0 |
| cached_artifact_only_family_count | 2 |
| no_training_required_family_count | 2 |
| multi_seed_family_count | 1 |
| single_seed_family_count | 1 |

## Checks

| Family | Check | Expected | Actual | Status | Detail |
| --- | --- | --- | --- | --- | --- |
| registry | schema_version | 1 | 1 | pass | Honest measurement contract holds. |
| registry | scope | engineering_governance_lane_only | engineering_governance_lane_only | pass | Honest measurement contract holds. |
| registry | family_count | >=1 | 2 | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | family_id_present | non-empty unique id | baseline-candidate-handoff-v433-v434 | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | cached_artifact_only | true | True | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | no_training_required | true | True | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | promotion_authority | none | none | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | promotion_ready_expected | false | False | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | seed_evidence_mode | single_seed\|multi_seed\|not_applicable | single_seed | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | single_seed_label | exploratory/not_claimed/no_promotion | exploratory_no_promotion | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | source_artifacts_present | non-empty list | 2 | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | source_artifacts[0] | exists inside project | d/433/解释/baseline-candidate-handoff/baseline_candidate_handoff.json | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | source_artifacts[1] | exists inside project | d/434/解释/baseline-candidate-handoff-check/baseline_candidate_handoff_check.json | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | contract_test_modules_present | non-empty list | 2 | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | contract_test_modules[0] | exists inside project | tests/test_baseline_candidate_handoff.py | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | contract_test_modules[1] | exists inside project | tests/test_baseline_candidate_handoff_check.py | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | positive_test_markers_present | non-empty list | 2 | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | marker:test_valid_handoff_check_passes_when_candidate_is_rejected | present in contract tests | test_valid_handoff_check_passes_when_candidate_is_rejected | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | marker:test_builder_check_out_dir_writes_sidecar | present in contract tests | test_builder_check_out_dir_writes_sidecar | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | negative_test_markers_present | non-empty list | 3 | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | marker:test_tampered_next_baseline_source_fails | present in contract tests | test_tampered_next_baseline_source_fails | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | marker:test_missing_source_loop_report_fails | present in contract tests | test_missing_source_loop_report_fails | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | marker:test_cli_require_pass_returns_one_on_failed_check | present in contract tests | test_cli_require_pass_returns_one_on_failed_check | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_guard[0].path | exists | d/433/解释/baseline-candidate-handoff/baseline_candidate_handoff.json | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:status | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:decision | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:source_loop_report | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:boundary | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:next_baseline | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_value:boundary.model_quality_claim | not_claimed | not_claimed | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_guard[1].path | exists | d/434/解释/baseline-candidate-handoff-check/baseline_candidate_handoff_check.json | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:status | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:decision | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:failed_count | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:source_handoff | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_field:source_loop_report | present | present | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_value:status | pass | pass | pass | Honest measurement contract holds. |
| baseline-candidate-handoff-v433-v434 | artifact_value:failed_count | 0 | 0 | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | family_id_present | non-empty unique id | route-promotion-release-readiness-v1258-v1259 | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | cached_artifact_only | true | True | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | no_training_required | true | True | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | promotion_authority | none | none | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | promotion_ready_expected | false | False | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | seed_evidence_mode | single_seed\|multi_seed\|not_applicable | multi_seed | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | multi_seed_count | >=2 | 3 | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | source_artifacts_present | non-empty list | 2 | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | source_artifacts[0] | exists inside project | f/1258/解释/model-capability-route-promotion-release-readiness-receipt-index/model_capability_route_promotion_release_readiness_receipt_index.json | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | source_artifacts[1] | exists inside project | f/1259/解释/model-capability-route-promotion-release-readiness-receipt-index-review/model_capability_route_promotion_release_readiness_receipt_index_review.json | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | contract_test_modules_present | non-empty list | 2 | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | contract_test_modules[0] | exists inside project | tests/test_model_capability_route_promotion_release_readiness_summary_check.py | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | contract_test_modules[1] | exists inside project | tests/test_model_capability_route_promotion_decision_index_check.py | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | positive_test_markers_present | non-empty list | 2 | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | marker:test_contract_check_passes_for_ready_summary | present in contract tests | test_contract_check_passes_for_ready_summary | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | marker:test_contract_check_passes_for_rebuildable_index | present in contract tests | test_contract_check_passes_for_rebuildable_index | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | negative_test_markers_present | non-empty list | 3 | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | marker:test_contract_check_fails_when_source_path_is_missing | present in contract tests | test_contract_check_fails_when_source_path_is_missing | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | marker:test_contract_check_fails_when_claim_widens | present in contract tests | test_contract_check_fails_when_claim_widens | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | marker:test_contract_check_fails_when_route_entry_is_tampered | present in contract tests | test_contract_check_fails_when_route_entry_is_tampered | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_guard[0].path | exists | f/1259/解释/model-capability-route-promotion-release-readiness-receipt-index-review/model_capability_route_promotion_release_readiness_receipt_index_review.json | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_field:status | present | present | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_field:decision | present | present | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_field:failed_count | present | present | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_field:source_receipt_index_summary | present | present | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_field:source_receipt_index | present | present | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_value:status | pass | pass | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_value:failed_count | 0 | 0 | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_value:source_receipt_index_summary.promotion_ready | False | False | pass | Honest measurement contract holds. |
| route-promotion-release-readiness-v1258-v1259 | artifact_value:source_receipt_index_summary.approved_for_promotion | False | False | pass | Honest measurement contract holds. |

## Recommendations

- Keep new capability families registered before claiming bounded model capability progress.

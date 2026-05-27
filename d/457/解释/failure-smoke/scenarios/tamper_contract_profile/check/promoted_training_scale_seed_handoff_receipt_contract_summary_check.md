# Promoted Seed Handoff Receipt Contract Summary Check

- Status: `fail`
- Decision: `continue`
- Actual summary status: `pass`
- Expected summary status: `pass`
- Sidecar status: `pass`
- Failed summary field checks: `1`
- Failed contract profile checks: `1`
- Failed check targets: `2`
- Failed sidecar checks: `0`
- Issue count: `2`

## Summary Field Checks

| Field | Type | Target | Status |
| --- | --- | --- | --- |
| contract_summary_version | summary_field | summary.contract_summary_version | pass |
| status | summary_field | summary.status | pass |
| decision | summary_field | summary.decision | pass |
| checker_exit_code | summary_field | summary.checker_exit_code | pass |
| handoff_report_path | summary_field | summary.handoff_report_path | pass |
| receipt_schema_version | summary_field | summary.receipt_schema_version | pass |
| schema_v3_ready | summary_field | summary.schema_v3_ready | pass |
| schema_v4_ready | summary_field | summary.schema_v4_ready | pass |
| assurance_status | summary_field | summary.assurance_status | pass |
| embedded_receipt_check_status | summary_field | summary.embedded_receipt_check_status | pass |
| embedded_receipt_check_sidecar_status | summary_field | summary.embedded_receipt_check_sidecar_status | pass |
| main_embedded_receipt_check_status | summary_field | summary.main_embedded_receipt_check_status | pass |
| receipt_check_output_json_exists | summary_field | summary.receipt_check_output_json_exists | pass |
| receipt_check_output_text_exists | summary_field | summary.receipt_check_output_text_exists | pass |
| suite_design_scopes | summary_field | summary.suite_design_scopes | pass |
| ci_boundary_plan_check_scopes | summary_field | summary.ci_boundary_plan_check_scopes | pass |
| contract_checks | summary_field | summary.contract_checks | pass |
| contract_check_count | summary_field | summary.contract_check_count | pass |
| failed_contract_check_count | summary_field | summary.failed_contract_check_count | pass |
| contract_check_status_counts | summary_field | summary.contract_check_status_counts | pass |
| contract_check_type_summary | summary_field | summary.contract_check_type_summary | fail |
| issue_count | summary_field | summary.issue_count | pass |
| issues | summary_field | summary.issues | pass |

## Check Family Summary

| Family | Status | Checks | Failed | Required failed | Failed targets |
| --- | --- | --- | --- | --- | --- |
| summary_field | fail | 23 | 1 | 1 | ["summary.contract_check_type_summary"] |
| contract_profile | fail | 4 | 1 | 1 | ["summary.contract_check_type_summary"] |
| sidecar | pass | 3 | 0 | 0 | [] |

## Failed Check Targets

| Family | Type | Target | Required | Detail |
| --- | --- | --- | --- | --- |
| summary_field | summary_field | summary.contract_check_type_summary | True | field differs from rebuilt summary |
| contract_profile | contract_profile_consistency | summary.contract_check_type_summary | True | contract check type summary must be derived from the embedded contract check rows; aggregate differs from rows |

## Contract Profile Checks

| Field | Type | Target | Status |
| --- | --- | --- | --- |
| contract_check_count | contract_profile_consistency | summary.contract_check_count | pass |
| failed_contract_check_count | contract_profile_consistency | summary.failed_contract_check_count | pass |
| contract_check_status_counts | contract_profile_consistency | summary.contract_check_status_counts | pass |
| contract_check_type_summary | contract_profile_consistency | summary.contract_check_type_summary | fail |

## Sidecar Checks

| Sidecar | Type | Target | Status | Exists |
| --- | --- | --- | --- | --- |
| text | sidecar_digest | d\457\解释\failure-smoke\scenarios\tamper_contract_profile\summary\promoted_training_scale_seed_handoff_receipt_contract_summary.txt | pass | True |
| markdown | sidecar_digest | d\457\解释\failure-smoke\scenarios\tamper_contract_profile\summary\promoted_training_scale_seed_handoff_receipt_contract_summary.md | pass | True |
| html | sidecar_digest | d\457\解释\failure-smoke\scenarios\tamper_contract_profile\summary\promoted_training_scale_seed_handoff_receipt_contract_summary.html | pass | True |

## Sidecars

- Text exists: `True`
- Markdown exists: `True`
- HTML exists: `True`

## Issues

- contract profile summary.contract_check_type_summary expected [{'check_type': 'count_consistency', 'count': 3, 'failed_count': 0, 'passed_count': 3, 'required_count': 3, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 3, 'targets': ['suite_design.comparison_ready.count_matches_names', 'suite_design.handoff.count_matches_names', 'suite_design.selected.count_matches_names']}, {'check_type': 'schema_readiness', 'count': 2, 'failed_count': 0, 'passed_count': 2, 'required_count': 2, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 2, 'targets': ['receipt.schema_v3_ready', 'receipt.schema_v4_ready']}, {'check_type': 'selected_within_handoff', 'count': 3, 'failed_count': 0, 'passed_count': 3, 'required_count': 3, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 3, 'targets': ['ci_boundary_plan_check.comparison_ready.selected_within_handoff', 'ci_boundary_plan_check.handoff.selected_within_handoff', 'ci_boundary_plan_check.selected.selected_within_handoff']}, {'check_type': 'status_equals', 'count': 2, 'failed_count': 0, 'passed_count': 2, 'required_count': 2, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 2, 'targets': ['assurance.status', 'embedded_receipt_check.sidecar_status']}] but got [{'check_type': 'count_consistency', 'count': 3, 'failed_count': 7, 'passed_count': 3, 'required_count': 3, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 3, 'targets': ['suite_design.comparison_ready.count_matches_names', 'suite_design.handoff.count_matches_names', 'suite_design.selected.count_matches_names']}, {'check_type': 'schema_readiness', 'count': 2, 'failed_count': 0, 'passed_count': 2, 'required_count': 2, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 2, 'targets': ['receipt.schema_v3_ready', 'receipt.schema_v4_ready']}, {'check_type': 'selected_within_handoff', 'count': 3, 'failed_count': 0, 'passed_count': 3, 'required_count': 3, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 3, 'targets': ['ci_boundary_plan_check.comparison_ready.selected_within_handoff', 'ci_boundary_plan_check.handoff.selected_within_handoff', 'ci_boundary_plan_check.selected.selected_within_handoff']}, {'check_type': 'status_equals', 'count': 2, 'failed_count': 0, 'passed_count': 2, 'required_count': 2, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 2, 'targets': ['assurance.status', 'embedded_receipt_check.sidecar_status']}]
- summary.contract_check_type_summary expected [{'check_type': 'count_consistency', 'count': 3, 'failed_count': 0, 'passed_count': 3, 'required_count': 3, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 3, 'targets': ['suite_design.comparison_ready.count_matches_names', 'suite_design.handoff.count_matches_names', 'suite_design.selected.count_matches_names']}, {'check_type': 'schema_readiness', 'count': 2, 'failed_count': 0, 'passed_count': 2, 'required_count': 2, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 2, 'targets': ['receipt.schema_v3_ready', 'receipt.schema_v4_ready']}, {'check_type': 'selected_within_handoff', 'count': 3, 'failed_count': 0, 'passed_count': 3, 'required_count': 3, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 3, 'targets': ['ci_boundary_plan_check.comparison_ready.selected_within_handoff', 'ci_boundary_plan_check.handoff.selected_within_handoff', 'ci_boundary_plan_check.selected.selected_within_handoff']}, {'check_type': 'status_equals', 'count': 2, 'failed_count': 0, 'passed_count': 2, 'required_count': 2, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 2, 'targets': ['assurance.status', 'embedded_receipt_check.sidecar_status']}] but got [{'check_type': 'count_consistency', 'count': 3, 'failed_count': 7, 'passed_count': 3, 'required_count': 3, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 3, 'targets': ['suite_design.comparison_ready.count_matches_names', 'suite_design.handoff.count_matches_names', 'suite_design.selected.count_matches_names']}, {'check_type': 'schema_readiness', 'count': 2, 'failed_count': 0, 'passed_count': 2, 'required_count': 2, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 2, 'targets': ['receipt.schema_v3_ready', 'receipt.schema_v4_ready']}, {'check_type': 'selected_within_handoff', 'count': 3, 'failed_count': 0, 'passed_count': 3, 'required_count': 3, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 3, 'targets': ['ci_boundary_plan_check.comparison_ready.selected_within_handoff', 'ci_boundary_plan_check.handoff.selected_within_handoff', 'ci_boundary_plan_check.selected.selected_within_handoff']}, {'check_type': 'status_equals', 'count': 2, 'failed_count': 0, 'passed_count': 2, 'required_count': 2, 'status': 'pass', 'status_domain': ['pass', 'fail'], 'target_count': 2, 'targets': ['assurance.status', 'embedded_receipt_check.sidecar_status']}]

# Promoted Seed Handoff Receipt Contract Summary Check

- Status: `pass`
- Decision: `continue`
- Actual summary status: `pass`
- Expected summary status: `pass`
- Sidecar status: `pass`
- Failed summary field checks: `0`
- Failed contract profile checks: `0`
- Failed check targets: `0`
- Failed sidecar checks: `0`
- Issue count: `0`

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
| contract_check_type_summary | summary_field | summary.contract_check_type_summary | pass |
| issue_count | summary_field | summary.issue_count | pass |
| issues | summary_field | summary.issues | pass |

## Check Family Summary

| Family | Status | Checks | Failed | Required failed | Failed targets |
| --- | --- | --- | --- | --- | --- |
| summary_field | pass | 23 | 0 | 0 | [] |
| contract_profile | pass | 4 | 0 | 0 | [] |
| sidecar | pass | 3 | 0 | 0 | [] |

## Failed Check Targets

| Family | Type | Target | Required | Detail |
| --- | --- | --- | --- | --- |
| none | none | none | none | none |

## Contract Profile Checks

| Field | Type | Target | Status |
| --- | --- | --- | --- |
| contract_check_count | contract_profile_consistency | summary.contract_check_count | pass |
| failed_contract_check_count | contract_profile_consistency | summary.failed_contract_check_count | pass |
| contract_check_status_counts | contract_profile_consistency | summary.contract_check_status_counts | pass |
| contract_check_type_summary | contract_profile_consistency | summary.contract_check_type_summary | pass |

## Sidecar Checks

| Sidecar | Type | Target | Status | Exists |
| --- | --- | --- | --- | --- |
| text | sidecar_digest | d\456\解释\contract-summary\promoted_training_scale_seed_handoff_receipt_contract_summary.txt | pass | True |
| markdown | sidecar_digest | d\456\解释\contract-summary\promoted_training_scale_seed_handoff_receipt_contract_summary.md | pass | True |
| html | sidecar_digest | d\456\解释\contract-summary\promoted_training_scale_seed_handoff_receipt_contract_summary.html | pass | True |

## Sidecars

- Text exists: `True`
- Markdown exists: `True`
- HTML exists: `True`

## Issues

- none

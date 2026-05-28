# Promoted Seed Handoff Receipt Contract Summary

- Status: `pass`
- Decision: `continue`
- Receipt schema version: `5`
- Schema v3 ready: `True`
- Schema v4 ready: `True`
- Schema v5 ready: `True`
- Assurance status: `pass`
- Embedded sidecar status: `pass`

## Suite-Design Scopes

| Scope | Count | Names | Count matches names |
| --- | ---: | --- | --- |
| selected | 0 | none | True |
| handoff | 0 | none | True |
| comparison_ready | 0 | none | True |

## CI Boundary Plan-Check Scopes

| Scope | Handoff count | Selected count | Selected within handoff |
| --- | ---: | ---: | --- |
| selected | 1 | 1 | True |
| handoff | 1 | 1 | True |
| comparison_ready | 0 | 0 | True |

## CI Reason-Count Scopes

| Scope | Handoff reasons | Selected reasons | Selected within handoff | Missing reasons |
| --- | --- | --- | --- | --- |
| selected | {"archived_path_portability_check_not_ready": 1} | {"archived_path_portability_check_not_ready": 1} | True | none |
| handoff | {"archived_path_portability_check_not_ready": 1, "workflow-order-regressed": 1} | {"archived_path_portability_check_not_ready": 1} | True | none |
| comparison_ready | {} | {} | True | none |

## Issues

- none

## Contract Checks

| Check | Type | Target | Scope | Status | Expected | Actual |
| --- | --- | --- | --- | --- | --- | --- |
| assurance_status_pass | status_equals | assurance.status | assurance | pass | pass | pass |
| schema_v3_ready | schema_readiness | receipt.schema_v3_ready | receipt | pass | True | True |
| schema_v4_ready | schema_readiness | receipt.schema_v4_ready | receipt | pass | True | True |
| schema_v5_ready | schema_readiness | receipt.schema_v5_ready | receipt | pass | True | True |
| embedded_receipt_check_sidecar_pass | status_equals | embedded_receipt_check.sidecar_status | embedded_receipt_check | pass | pass | pass |
| suite_design_selected_count_matches_names | count_consistency | suite_design.selected.count_matches_names | selected | pass | True | True |
| suite_design_handoff_count_matches_names | count_consistency | suite_design.handoff.count_matches_names | handoff | pass | True | True |
| suite_design_comparison_ready_count_matches_names | count_consistency | suite_design.comparison_ready.count_matches_names | comparison_ready | pass | True | True |
| ci_boundary_plan_check_selected_selected_within_handoff | selected_within_handoff | ci_boundary_plan_check.selected.selected_within_handoff | selected | pass | True | True |
| ci_boundary_plan_check_handoff_selected_within_handoff | selected_within_handoff | ci_boundary_plan_check.handoff.selected_within_handoff | handoff | pass | True | True |
| ci_boundary_plan_check_comparison_ready_selected_within_handoff | selected_within_handoff | ci_boundary_plan_check.comparison_ready.selected_within_handoff | comparison_ready | pass | True | True |
| ci_reason_counts_selected_selected_within_handoff | reason_counts_within_handoff | ci_reason_counts.selected.selected_reasons_within_handoff | selected | pass | True | True |
| ci_reason_counts_handoff_selected_within_handoff | reason_counts_within_handoff | ci_reason_counts.handoff.selected_reasons_within_handoff | handoff | pass | True | True |
| ci_reason_counts_comparison_ready_selected_within_handoff | reason_counts_within_handoff | ci_reason_counts.comparison_ready.selected_reasons_within_handoff | comparison_ready | pass | True | True |

## Contract Check Type Summary

| Type | Status | Count | Passed | Failed | Required | Targets |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| count_consistency | pass | 3 | 3 | 0 | 3 | suite_design.comparison_ready.count_matches_names, suite_design.handoff.count_matches_names, suite_design.selected.count_matches_names |
| reason_counts_within_handoff | pass | 3 | 3 | 0 | 3 | ci_reason_counts.comparison_ready.selected_reasons_within_handoff, ci_reason_counts.handoff.selected_reasons_within_handoff, ci_reason_counts.selected.selected_reasons_within_handoff |
| schema_readiness | pass | 3 | 3 | 0 | 3 | receipt.schema_v3_ready, receipt.schema_v4_ready, receipt.schema_v5_ready |
| selected_within_handoff | pass | 3 | 3 | 0 | 3 | ci_boundary_plan_check.comparison_ready.selected_within_handoff, ci_boundary_plan_check.handoff.selected_within_handoff, ci_boundary_plan_check.selected.selected_within_handoff |
| status_equals | pass | 2 | 2 | 0 | 2 | assurance.status, embedded_receipt_check.sidecar_status |

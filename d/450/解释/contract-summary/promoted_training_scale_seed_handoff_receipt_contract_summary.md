# Promoted Seed Handoff Receipt Contract Summary

- Status: `pass`
- Decision: `continue`
- Receipt schema version: `4`
- Schema v3 ready: `True`
- Schema v4 ready: `True`
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
| selected | 0 | 0 | True |
| handoff | 1 | 1 | True |
| comparison_ready | 0 | 0 | True |

## Issues

- none

## Contract Checks

| Check | Scope | Status | Expected | Actual |
| --- | --- | --- | --- | --- |
| assurance_status_pass | assurance | pass | pass | pass |
| schema_v3_ready | receipt | pass | True | True |
| schema_v4_ready | receipt | pass | True | True |
| embedded_receipt_check_sidecar_pass | embedded_receipt_check | pass | pass | pass |
| suite_design_selected_count_matches_names | selected | pass | True | True |
| suite_design_handoff_count_matches_names | handoff | pass | True | True |
| suite_design_comparison_ready_count_matches_names | comparison_ready | pass | True | True |
| ci_boundary_plan_check_selected_selected_within_handoff | selected | pass | True | True |
| ci_boundary_plan_check_handoff_selected_within_handoff | handoff | pass | True | True |
| ci_boundary_plan_check_comparison_ready_selected_within_handoff | comparison_ready | pass | True | True |

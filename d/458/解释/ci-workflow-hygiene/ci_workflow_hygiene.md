# MiniGPT CI workflow hygiene

- Generated: `2026-05-27T05:57:58Z`
- Workflow: `.github\workflows\ci.yml`
- Status: `pass`
- Decision: `continue_with_node24_native_ci`

## Summary

| Metric | Value |
| --- | --- |
| check_count | 29 |
| passed_check_count | 29 |
| failed_check_count | 0 |
| action_count | 2 |
| found_required_action_count | 2 |
| node24_native_action_count | 2 |
| forbidden_env_count | 0 |
| missing_step_count | 0 |
| order_violation_count | 0 |
| tiny_scorecard_plan_digest_gate_present | True |
| tiny_scorecard_plan_digest_gate_order_ready | True |
| tiny_scorecard_plan_digest_gate_ready | True |
| baseline_candidate_threshold_boundary_gate_check_present | True |
| baseline_candidate_threshold_boundary_gate_check_order_ready | True |
| baseline_candidate_threshold_boundary_gate_check_ready | True |
| baseline_candidate_threshold_boundary_gate_plan_check_present | True |
| baseline_candidate_threshold_boundary_gate_plan_check_order_ready | True |
| baseline_candidate_threshold_boundary_gate_plan_check_ready | True |
| promoted_seed_receipt_contract_failure_smoke_present | True |
| promoted_seed_receipt_contract_failure_smoke_order_ready | True |
| promoted_seed_receipt_contract_failure_smoke_ready | True |
| release_readiness_drift_contract_smoke_present | True |
| release_readiness_drift_contract_smoke_order_ready | True |
| release_readiness_drift_contract_smoke_ready | True |
| python_version | 3.11 |

## Checks

| ID | Category | Target | Expected | Actual | Status | Detail |
| --- | --- | --- | --- | --- | --- | --- |
| action:actions/checkout | action_version | actions/checkout | v6 | v6 | pass | Action uses the expected Node 24 native major. |
| action:actions/setup-python | action_version | actions/setup-python | v6 | v6 | pass | Action uses the expected Node 24 native major. |
| env:FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 | forbidden_env | FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 | absent | absent | pass | Native action versions should not rely on force-runtime environment variables. |
| command:source_encoding_gate | required_command | source_encoding_gate | scripts/check_source_encoding.py | present | pass | Required CI quality command is present. |
| command:ci_workflow_hygiene_gate | required_command | ci_workflow_hygiene_gate | scripts/check_ci_workflow_hygiene.py | present | pass | Required CI quality command is present. |
| command:promoted_seed_handoff_assurance_smoke | required_command | promoted_seed_handoff_assurance_smoke | scripts/check_promoted_seed_handoff_assurance_smoke.py | present | pass | Required CI quality command is present. |
| command:promoted_seed_receipt_contract_summary | required_command | promoted_seed_receipt_contract_summary | scripts/check_promoted_seed_handoff_receipt_contract.py | present | pass | Required CI quality command is present. |
| command:promoted_seed_receipt_contract_summary_check_failure_smoke | required_command | promoted_seed_receipt_contract_summary_check_failure_smoke | scripts/smoke_promoted_seed_handoff_receipt_contract_summary_check_failures.py | present | pass | Required CI quality command is present. |
| command:tiny_scorecard_comparison_inline_check_smoke | required_command | tiny_scorecard_comparison_inline_check_smoke | scripts/run_ci_tiny_scorecard_comparison_smoke.py | present | pass | Required CI quality command is present. |
| command:tiny_scorecard_summary_check_sidecar | required_command | tiny_scorecard_summary_check_sidecar | --summary-check-out-dir | present | pass | Required CI quality command is present. |
| command:ci_tiny_scorecard_plan_digest_check | required_command | ci_tiny_scorecard_plan_digest_check | scripts/check_ci_tiny_scorecard_plan.py | present | pass | Required CI quality command is present. |
| command:baseline_candidate_threshold_boundary_gate_check | required_command | baseline_candidate_threshold_boundary_gate_check | scripts/run_ci_baseline_candidate_threshold_boundary_gate_check.py | present | pass | Required CI quality command is present. |
| command:baseline_candidate_threshold_boundary_gate_plan_check | required_command | baseline_candidate_threshold_boundary_gate_plan_check | scripts/check_ci_baseline_candidate_threshold_boundary_gate_plan.py | present | pass | Required CI quality command is present. |
| command:release_readiness_drift_contract_smoke | required_command | release_readiness_drift_contract_smoke | scripts/check_release_readiness_drift_contract_smoke.py | present | pass | Required CI quality command is present. |
| command:test_coverage_report | required_command | test_coverage_report | scripts/run_test_coverage.py | present | pass | Required CI quality command is present. |
| command:coverage_fail_under_gate | required_command | coverage_fail_under_gate | --fail-under 80 | present | pass | Required CI quality command is present. |
| order:promoted_seed_handoff_assurance_smoke_before_coverage | required_order | promoted_seed_handoff_assurance_smoke_before_coverage | before | before_line=30;after_line=53 | pass | Required CI command order is preserved: before line 30, after line 53. |
| order:tiny_scorecard_inline_check_smoke_before_coverage | required_order | tiny_scorecard_inline_check_smoke_before_coverage | before | before_line=38;after_line=53 | pass | Required CI command order is preserved: before line 38, after line 53. |
| order:promoted_seed_receipt_contract_summary_after_assurance | required_order | promoted_seed_receipt_contract_summary_after_assurance | before | before_line=30;after_line=34 | pass | Required CI command order is preserved: before line 30, after line 34. |
| order:promoted_seed_receipt_contract_failure_smoke_after_summary | required_order | promoted_seed_receipt_contract_failure_smoke_after_summary | before | before_line=34;after_line=35 | pass | Required CI command order is preserved: before line 34, after line 35. |
| order:promoted_seed_receipt_contract_failure_smoke_before_coverage | required_order | promoted_seed_receipt_contract_failure_smoke_before_coverage | before | before_line=35;after_line=53 | pass | Required CI command order is preserved: before line 35, after line 53. |
| order:ci_tiny_scorecard_plan_check_after_smoke | required_order | ci_tiny_scorecard_plan_check_after_smoke | before | before_line=38;after_line=41 | pass | Required CI command order is preserved: before line 38, after line 41. |
| order:ci_tiny_scorecard_plan_check_before_coverage | required_order | ci_tiny_scorecard_plan_check_before_coverage | before | before_line=41;after_line=53 | pass | Required CI command order is preserved: before line 41, after line 53. |
| order:baseline_candidate_threshold_boundary_gate_check_after_plan_digest | required_order | baseline_candidate_threshold_boundary_gate_check_after_plan_digest | before | before_line=41;after_line=44 | pass | Required CI command order is preserved: before line 41, after line 44. |
| order:baseline_candidate_threshold_boundary_gate_check_before_coverage | required_order | baseline_candidate_threshold_boundary_gate_check_before_coverage | before | before_line=44;after_line=53 | pass | Required CI command order is preserved: before line 44, after line 53. |
| order:baseline_candidate_threshold_boundary_gate_plan_check_after_gate_check | required_order | baseline_candidate_threshold_boundary_gate_plan_check_after_gate_check | before | before_line=44;after_line=47 | pass | Required CI command order is preserved: before line 44, after line 47. |
| order:baseline_candidate_threshold_boundary_gate_plan_check_before_coverage | required_order | baseline_candidate_threshold_boundary_gate_plan_check_before_coverage | before | before_line=47;after_line=53 | pass | Required CI command order is preserved: before line 47, after line 53. |
| order:release_readiness_drift_contract_smoke_before_coverage | required_order | release_readiness_drift_contract_smoke_before_coverage | before | before_line=50;after_line=53 | pass | Required CI command order is preserved: before line 50, after line 53. |
| python:setup-version | python_version | actions/setup-python | 3.11 | 3.11 | pass | CI parser target should remain aligned with source encoding compatibility checks. |

## Actions

| Repository | Version | Line | Node 24 Native |
| --- | --- | --- | --- |
| actions/checkout | v6 | 12 | True |
| actions/setup-python | v6 | 14 | True |

## Recommendations

- Keep CI workflow action versions and quality gates aligned with the Node 24 native policy.

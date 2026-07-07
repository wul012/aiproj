# MiniGPT File Size Ratchet

- Generated: `2026-07-07T05:53:08Z`
- Status: `pass`
- Decision: `continue_with_file_size_ratchet`
- Config: `docs/code-health/file-size-ratchet.json`

## Summary

| Metric | Value |
| --- | --- |
| scanned_file_count | 2773 |
| warning_line_limit | 500 |
| max_line_limit | 800 |
| over_warning_count | 20 |
| over_limit_count | 8 |
| waiver_count | 8 |
| unwaived_over_limit_count | 0 |
| waiver_growth_violation_count | 0 |
| largest_file_path | tests/test_promoted_training_scale_seed_handoff.py |
| largest_file_lines | 1398 |
| failed_check_count | 0 |

## Oversize Files

| Path | Lines | Waived | Waiver Status |
| --- | ---: | --- | --- |
| tests/test_promoted_training_scale_seed_handoff.py | 1398 | True | at_baseline |
| tests/test_promoted_training_scale_seed_handoff_receipt.py | 1281 | True | at_baseline |
| tests/test_registry.py | 944 | True | at_baseline |
| tests/test_maturity_narrative.py | 894 | True | at_baseline |
| tests/test_release_readiness_comparison.py | 873 | True | at_baseline |
| tests/test_promoted_training_scale_decision.py | 838 | True | at_baseline |
| tests/test_promoted_training_scale_seed.py | 836 | True | at_baseline |
| tests/test_server.py | 815 | True | at_baseline |
| tests/test_promoted_training_scale_comparison.py | 719 | False | not_waived |
| tests/test_project_audit.py | 700 | False | not_waived |
| tests/test_release_readiness.py | 688 | False | not_waived |
| tests/test_tiny_scorecard_comparison_smoke.py | 645 | False | not_waived |
| tests/test_release_bundle.py | 627 | False | not_waived |
| tests/test_release_gate.py | 612 | False | not_waived |
| tests/test_training_scale_promotion.py | 597 | False | not_waived |
| tests/test_maturity.py | 590 | False | not_waived |
| tests/test_training_portfolio_comparison.py | 570 | False | not_waived |
| tests/test_maintenance_policy.py | 539 | False | not_waived |
| tests/test_training_scale_promotion_index.py | 535 | False | not_waived |
| scripts/execute_promoted_training_scale_seed.py | 514 | False | not_waived |

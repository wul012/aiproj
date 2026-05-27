# MiniGPT release bundle

- Release: `v461-receipt-plan-carryover`
- Generated: `2026-05-27T08:31:35Z`

## Summary

| Field | Value |
| --- | --- |
| Release status | release-ready |
| Audit status | pass |
| Audit score | 100 |
| Run count | 1 |
| Best run | v461-receipt-plan-carryover |
| Best val loss | 0.8 |
| Ready runs | 1 |
| Request history status | pass |
| Benchmark history status | pass |
| Benchmark history entries | 1 |
| Benchmark history ready | 1 |
| Benchmark history regressions | 0 |
| Benchmark history suite-design not-ready | 0 |
| Benchmark history design changes | 0 |
| Benchmark history readiness | pass |
| Benchmark history readiness exit | 0 |
| Benchmark history readiness reasons | none |
| Benchmark history boundary | standard-benchmark-candidate-evidence |
| CI workflow status | pass |
| CI workflow failed checks | 0 |
| CI workflow required order | 4 |
| CI workflow order violations | 0 |
| CI tiny plan digest gate | True |
| CI boundary gate check | True |
| CI boundary plan check | True |
| CI receipt failure-smoke plan check | True |
| CI drift contract smoke | True |
| Test coverage status | pass |
| Test coverage percent | 90.16 |
| Test coverage fail under | 80 |
| Test coverage gap | 0 |
| Evidence artifacts | 13 |

## Inputs

| Field | Value |
| --- | --- |
| registry_path | D:\aiproj\d\461\解释\source-inputs\registry\registry.json |
| model_card_path | D:\aiproj\d\461\解释\source-inputs\model-card\model_card.json |
| project_audit_path | D:\aiproj\d\461\解释\project-audit-carryover\project_audit.json |
| request_history_summary_path | D:\aiproj\d\461\解释\source-inputs\request-history-summary\request_history_summary.json |
| benchmark_history_path | D:\aiproj\d\461\解释\source-inputs\benchmark-history\benchmark_history.json |
| ci_workflow_hygiene_path | D:\aiproj\d\461\解释\source-inputs\ci-workflow-hygiene\ci_workflow_hygiene.json |
| test_coverage_report_path | D:\aiproj\d\461\解释\source-inputs\test-coverage\test_coverage_report.json |

## Top Runs

| Rank | Run | Status | Best Val | Delta | Quality | Eval |
| --- | --- | --- | --- | --- | --- | --- |
| #1 | v461-receipt-plan-carryover | missing | 0.8 | +0 | pass | 3 |

## Audit Checks

| Status | Check | Detail |
| --- | --- | --- |
| pass | Registry has runs | 1 registered run(s). |
| pass | Best run is identified | best=v461-receipt-plan-carryover |
| pass | Comparable loss coverage | 1/1 run(s). |
| pass | Experiment card coverage | 1/1 run(s). |
| pass | Dataset quality coverage | 1/1 run(s). |
| pass | Eval suite coverage | 1/1 run(s). |
| pass | Generation quality coverage | 1/1 run(s). |
| pass | Checkpoint coverage | 1/1 run(s). |
| pass | Dashboard coverage | 1/1 run(s). |
| pass | Model card is available | model_card.json loaded |
| pass | At least one ready run | 1 ready run(s). |
| pass | Request history summary is clean | status=pass; records=4; invalid=0; timeout_rate=0; error_rate=0. |
| pass | Benchmark history is audit-ready | entries=1; ready=1; review=0; blocked=0; case_regressions=0; generation_flag_regressions=0; suite_design_not_ready=0; design_comparison_changed=0; readiness_requirement=pass; readiness_exit=0; readiness_failed_reasons=none; model_quality_claim=candidate_evidence; latest_boundary=standard-benchmark-candidate-evidence. |
| pass | CI workflow hygiene is clean | status=pass; actions=2; node24_native=2; failed_checks=0; forbidden_env=0; missing_steps=0; order_violations=0; tiny_scorecard_plan_digest_gate_ready=True; baseline_candidate_threshold_boundary_gate_check_ready=True; baseline_candidate_threshold_boundary_gate_plan_check_ready=True; promoted_seed_receipt_contract_failure_smoke_plan_check_ready=True; release_readiness_drift_contract_smoke_ready=True. |
| pass | Test coverage gate is clean | status=pass; decision=continue_with_coverage_gate; line_coverage=90.16; fail_under=80; coverage_gap=0; threshold_enabled=True. |
| pass | No non-pass dataset quality runs | all checked runs pass |
| pass | No non-pass generation quality runs | all analyzed runs pass |

## Evidence Artifacts

- `D:\aiproj\d\461\解释\source-inputs\registry\registry.json`: yes, JSON, 730 bytes
- `D:\aiproj\d\461\解释\source-inputs\registry\registry.csv`: yes, CSV, 35 bytes
- `D:\aiproj\d\461\解释\source-inputs\registry\registry.svg`: no, SVG, missing
- `D:\aiproj\d\461\解释\source-inputs\registry\registry.html`: yes, HTML, 13 bytes
- `D:\aiproj\d\461\解释\source-inputs\model-card\model_card.json`: yes, JSON, 418 bytes
- `D:\aiproj\d\461\解释\source-inputs\model-card\model_card.md`: yes, MD, 12 bytes
- `D:\aiproj\d\461\解释\source-inputs\model-card\model_card.html`: yes, HTML, 13 bytes
- `D:\aiproj\d\461\解释\project-audit-carryover\project_audit.json`: yes, JSON, 14,649 bytes
- `D:\aiproj\d\461\解释\project-audit-carryover\project_audit.md`: yes, MD, 3,852 bytes
- `D:\aiproj\d\461\解释\project-audit-carryover\project_audit.html`: yes, HTML, 8,240 bytes
- `D:\aiproj\d\461\解释\source-inputs\request-history-summary\request_history_summary.json`: yes, JSON, 414 bytes
- `D:\aiproj\d\461\解释\source-inputs\request-history-summary\request_history_summary.md`: no, MD, missing
- `D:\aiproj\d\461\解释\source-inputs\request-history-summary\request_history_summary.html`: no, HTML, missing
- `D:\aiproj\d\461\解释\source-inputs\benchmark-history\benchmark_history.json`: yes, JSON, 1,106 bytes
- `D:\aiproj\d\461\解释\source-inputs\benchmark-history\benchmark_history.md`: no, MD, missing
- `D:\aiproj\d\461\解释\source-inputs\benchmark-history\benchmark_history.html`: no, HTML, missing
- `D:\aiproj\d\461\解释\source-inputs\ci-workflow-hygiene\ci_workflow_hygiene.json`: yes, JSON, 1,364 bytes
- `D:\aiproj\d\461\解释\source-inputs\ci-workflow-hygiene\ci_workflow_hygiene.md`: no, MD, missing
- `D:\aiproj\d\461\解释\source-inputs\ci-workflow-hygiene\ci_workflow_hygiene.html`: no, HTML, missing
- `D:\aiproj\d\461\解释\source-inputs\test-coverage\test_coverage_report.json`: yes, JSON, 327 bytes
- `D:\aiproj\d\461\解释\source-inputs\test-coverage\test_coverage_report.md`: no, MD, missing
- `D:\aiproj\d\461\解释\source-inputs\test-coverage\test_coverage_report.html`: no, HTML, missing

## Recommendations

- Release evidence is complete; keep this bundle with the tagged version.
- All audit checks passed; keep the audit with the model card as release evidence.

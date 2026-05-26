# MiniGPT release bundle

- Release: `v445-context-carryover`
- Generated: `2026-05-26T11:42:04Z`

## Summary

| Field | Value |
| --- | --- |
| Release status | release-ready |
| Audit status | pass |
| Audit score | 100 |
| Run count | 1 |
| Best run | v445-context-candidate |
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
| CI workflow required order | 9 |
| CI workflow order violations | 0 |
| CI tiny plan digest gate | True |
| CI boundary gate check | True |
| CI boundary plan check | True |
| CI drift contract smoke | True |
| Test coverage status | pass |
| Test coverage percent | 90.17 |
| Test coverage fail under | 80 |
| Test coverage gap | 0 |
| Evidence artifacts | 22 |

## Inputs

| Field | Value |
| --- | --- |
| registry_path | d\445\解释\context-inputs\registry\registry.json |
| model_card_path | d\445\解释\context-inputs\model-card\model_card.json |
| project_audit_path | d\445\解释\project-audit\project_audit.json |
| request_history_summary_path | d\445\解释\context-inputs\request-history-summary\request_history_summary.json |
| benchmark_history_path | d\445\解释\context-inputs\benchmark-history\benchmark_history.json |
| ci_workflow_hygiene_path | d\445\解释\ci-workflow-hygiene\ci_workflow_hygiene.json |
| test_coverage_report_path | d\445\解释\context-inputs\test-coverage\test_coverage_report.json |

## Top Runs

| Rank | Run | Status | Best Val | Delta | Quality | Eval |
| --- | --- | --- | --- | --- | --- | --- |
| unranked | v445-context-candidate | ready | 0.8 | missing | missing | missing |

## Audit Checks

| Status | Check | Detail |
| --- | --- | --- |
| pass | Registry has runs | 1 registered run(s). |
| pass | Best run is identified | best=v445-context-candidate |
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
| pass | CI workflow hygiene is clean | status=pass; actions=2; node24_native=2; failed_checks=0; forbidden_env=0; missing_steps=0; order_violations=0; tiny_scorecard_plan_digest_gate_ready=True; baseline_candidate_threshold_boundary_gate_check_ready=True; baseline_candidate_threshold_boundary_gate_plan_check_ready=True; release_readiness_drift_contract_smoke_ready=True. |
| pass | Test coverage gate is clean | status=pass; decision=continue_with_coverage_gate; line_coverage=90.17; fail_under=80; coverage_gap=0; threshold_enabled=True. |
| pass | No non-pass dataset quality runs | all checked runs pass |
| pass | No non-pass generation quality runs | all analyzed runs pass |

## Evidence Artifacts

- `d\445\解释\context-inputs\registry\registry.json`: yes, JSON, 930 bytes
- `d\445\解释\context-inputs\registry\registry.csv`: yes, CSV, 48 bytes
- `d\445\解释\context-inputs\registry\registry.svg`: yes, SVG, 78 bytes
- `d\445\解释\context-inputs\registry\registry.html`: yes, HTML, 41 bytes
- `d\445\解释\context-inputs\model-card\model_card.json`: yes, JSON, 933 bytes
- `d\445\解释\context-inputs\model-card\model_card.md`: yes, MD, 19 bytes
- `d\445\解释\context-inputs\model-card\model_card.html`: yes, HTML, 43 bytes
- `d\445\解释\project-audit\project_audit.json`: yes, JSON, 13,855 bytes
- `d\445\解释\project-audit\project_audit.md`: yes, MD, 3,652 bytes
- `d\445\解释\project-audit\project_audit.html`: yes, HTML, 8,037 bytes
- `d\445\解释\context-inputs\request-history-summary\request_history_summary.json`: yes, JSON, 441 bytes
- `d\445\解释\context-inputs\request-history-summary\request_history_summary.md`: yes, MD, 24 bytes
- `d\445\解释\context-inputs\request-history-summary\request_history_summary.html`: yes, HTML, 48 bytes
- `d\445\解释\context-inputs\benchmark-history\benchmark_history.json`: yes, JSON, 1,398 bytes
- `d\445\解释\context-inputs\benchmark-history\benchmark_history.md`: yes, MD, 26 bytes
- `d\445\解释\context-inputs\benchmark-history\benchmark_history.html`: yes, HTML, 50 bytes
- `d\445\解释\ci-workflow-hygiene\ci_workflow_hygiene.json`: yes, JSON, 13,858 bytes
- `d\445\解释\ci-workflow-hygiene\ci_workflow_hygiene.md`: yes, MD, 7,033 bytes
- `d\445\解释\ci-workflow-hygiene\ci_workflow_hygiene.html`: yes, HTML, 9,854 bytes
- `d\445\解释\context-inputs\test-coverage\test_coverage_report.json`: yes, JSON, 400 bytes
- `d\445\解释\context-inputs\test-coverage\test_coverage_report.md`: yes, MD, 22 bytes
- `d\445\解释\context-inputs\test-coverage\test_coverage_report.html`: yes, HTML, 46 bytes

## Recommendations

- Release evidence is complete; keep this bundle with the tagged version.
- All audit checks passed; keep the audit with the model card as release evidence.
- Keep v445 context carryover evidence with the tagged version.

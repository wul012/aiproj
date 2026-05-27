# MiniGPT release readiness dashboard

- Generated: `2026-05-27T11:38:41Z`
- Bundle: `d\464\解释\release-bundle-archived-path-carryover\release_bundle.json`

## Summary

| Field | Value |
| --- | --- |
| Readiness status | ready |
| Decision | ship |
| Release | v464-archived-path-portability-carryover |
| Gate | pass |
| Audit | pass |
| Audit score | 100 |
| CI workflow | pass |
| CI required order | 15 |
| CI order violations | 0 |
| CI tiny plan digest gate | True |
| CI boundary gate check | True |
| CI boundary plan check | True |
| CI archived path portability | True |
| CI receipt failure-smoke plan check | True |
| CI drift contract smoke | True |
| Request history | pass |
| Benchmark history | pass |
| Benchmark entries | 1 |
| Benchmark ready | 1 |
| Benchmark regressions | 0 |
| Benchmark history suite-design not-ready | 0 |
| Benchmark history design changes | 0 |
| Benchmark readiness | pass |
| Benchmark readiness exit | 0 |
| Benchmark readiness reasons | none |
| Benchmark boundary | standard-benchmark-candidate-evidence |
| Test coverage | pass |
| Coverage percent | 90.16 |
| Coverage fail under | 80 |
| Coverage gap | 0 |
| Maturity | pass |
| Ready runs | 1 |
| Missing artifacts | 7 |

## Panels

| Status | Panel | Detail | Source |
| --- | --- | --- | --- |
| pass | Registry | runs=1; best=v461-receipt-plan-carryover; best_val_loss=0.8 | d\461\解释\source-inputs\registry\registry.json |
| pass | Release Bundle | release_status=release-ready; artifacts=15 available/7 missing | d\464\解释\release-bundle-archived-path-carryover\release_bundle.json |
| pass | Project Audit | overall=pass; score=100; checks=17 pass/0 warn/0 fail | d\464\解释\project-audit-archived-path-carryover\project_audit.json |
| pass | Release Gate | gate=pass; decision=approved; checks=12 pass/0 warn/0 fail | d\461\解释\source-inputs\release-gate\gate_report.json |
| pass | Request History Summary | status=pass; records=4; invalid=0; timeout_rate=0 | d\461\解释\source-inputs\request-history-summary\request_history_summary.json |
| pass | Benchmark History | status=pass; entries=1; ready=1; review=0; blocked=0; case_regressions=0; generation_flag_regressions=0; suite_design_not_ready=0; design_comparison_changed=0; readiness_requirement=pass; readiness_exit=0; readiness_failed_reasons=none; model_quality_claim=candidate_evidence; boundary=standard-benchmark-candidate-evidence; gate_check=pass | missing |
| pass | Maturity Summary | overall=pass; current_version=461; average_level=4.6 | d\461\解释\source-inputs\maturity-summary\maturity_summary.json |
| pass | CI Workflow Hygiene | status=pass; failed_checks=0; node24_native=2; required_order=15; order_violations=0; plan_digest_gate_ready=True; boundary_gate_check_ready=True; boundary_gate_plan_check_ready=True; archived_path_portability_check_ready=True; receipt_failure_smoke_plan_check_ready=True; drift_contract_smoke_ready=True | d\464\解释\ci-workflow-hygiene\ci_workflow_hygiene.json |
| pass | Test Coverage Gate | status=pass; coverage=90.16; fail_under=80; gap=0 | d\461\解释\source-inputs\test-coverage\test_coverage_report.json |

## Actions

- All readiness panels are clean; keep this dashboard with the release evidence.
- All audit checks passed; keep the audit with the model card as release evidence.
- Release evidence is complete; keep this bundle with the tagged version.

## Evidence

- `d\461\解释\source-inputs\registry\registry.json`: yes, JSON, 730 B
- `d\461\解释\source-inputs\registry\registry.csv`: yes, CSV, 35 B
- `d\461\解释\source-inputs\registry\registry.svg`: no, SVG, missing
- `d\461\解释\source-inputs\registry\registry.html`: yes, HTML, 13 B
- `d\461\解释\source-inputs\model-card\model_card.json`: yes, JSON, 418 B
- `d\461\解释\source-inputs\model-card\model_card.md`: yes, MD, 12 B
- `d\461\解释\source-inputs\model-card\model_card.html`: yes, HTML, 13 B
- `d\464\解释\project-audit-archived-path-carryover\project_audit.json`: yes, JSON, 14.6 KB
- `d\464\解释\project-audit-archived-path-carryover\project_audit.md`: yes, MD, 3.8 KB
- `d\464\解释\project-audit-archived-path-carryover\project_audit.html`: yes, HTML, 8.2 KB
- `d\461\解释\source-inputs\request-history-summary\request_history_summary.json`: yes, JSON, 414 B
- `d\461\解释\source-inputs\request-history-summary\request_history_summary.md`: no, MD, missing
- `d\461\解释\source-inputs\request-history-summary\request_history_summary.html`: no, HTML, missing
- `d\461\解释\source-inputs\benchmark-history\benchmark_history.json`: yes, JSON, 1.1 KB
- `d\461\解释\source-inputs\benchmark-history\benchmark_history.md`: no, MD, missing
- `d\461\解释\source-inputs\benchmark-history\benchmark_history.html`: no, HTML, missing
- `d\464\解释\ci-workflow-hygiene\ci_workflow_hygiene.json`: yes, JSON, 19.3 KB
- `d\464\解释\ci-workflow-hygiene\ci_workflow_hygiene.md`: yes, MD, 9.7 KB
- `d\464\解释\ci-workflow-hygiene\ci_workflow_hygiene.html`: yes, HTML, 12.6 KB
- `d\461\解释\source-inputs\test-coverage\test_coverage_report.json`: yes, JSON, 327 B
- `d\461\解释\source-inputs\test-coverage\test_coverage_report.md`: no, MD, missing
- `d\461\解释\source-inputs\test-coverage\test_coverage_report.html`: no, HTML, missing

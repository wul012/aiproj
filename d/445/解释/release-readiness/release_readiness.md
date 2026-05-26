# MiniGPT release readiness dashboard

- Generated: `2026-05-26T11:45:14Z`
- Bundle: `d\445\解释\release-bundle\release_bundle.json`

## Summary

| Field | Value |
| --- | --- |
| Readiness status | ready |
| Decision | ship |
| Release | v445-context-carryover |
| Gate | pass |
| Audit | pass |
| Audit score | 100 |
| CI workflow | pass |
| CI required order | 9 |
| CI order violations | 0 |
| CI tiny plan digest gate | True |
| CI boundary gate check | True |
| CI boundary plan check | True |
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
| Coverage percent | 90.17 |
| Coverage fail under | 80 |
| Coverage gap | 0 |
| Maturity | pass |
| Ready runs | 1 |
| Missing artifacts | 0 |

## Panels

| Status | Panel | Detail | Source |
| --- | --- | --- | --- |
| pass | Registry | runs=1; best=v445-context-candidate; best_val_loss=0.8 | d\445\解释\context-inputs\registry\registry.json |
| pass | Release Bundle | release_status=release-ready; artifacts=22 available/0 missing | d\445\解释\release-bundle\release_bundle.json |
| pass | Project Audit | overall=pass; score=100; checks=17 pass/0 warn/0 fail | d\445\解释\project-audit\project_audit.json |
| pass | Release Gate | gate=pass; decision=approved; checks=14 pass/0 warn/0 fail | d\445\解释\release-gate\gate_report.json |
| pass | Request History Summary | status=pass; records=4; invalid=0; timeout_rate=0 | d\445\解释\context-inputs\request-history-summary\request_history_summary.json |
| pass | Benchmark History | status=pass; entries=1; ready=1; review=0; blocked=0; case_regressions=0; generation_flag_regressions=0; suite_design_not_ready=0; design_comparison_changed=0; readiness_requirement=pass; readiness_exit=0; readiness_failed_reasons=none; model_quality_claim=candidate_evidence; boundary=standard-benchmark-candidate-evidence; gate_check=pass | missing |
| pass | Maturity Summary | overall=pass; current_version=445; average_level=4.6 | d\445\解释\context-inputs\maturity-summary\maturity_summary.json |
| pass | CI Workflow Hygiene | status=pass; failed_checks=0; node24_native=2; required_order=9; order_violations=0; plan_digest_gate_ready=True; boundary_gate_check_ready=True; boundary_gate_plan_check_ready=True; drift_contract_smoke_ready=True | d\445\解释\ci-workflow-hygiene\ci_workflow_hygiene.json |
| pass | Test Coverage Gate | status=pass; coverage=90.17; fail_under=80; gap=0 | d\445\解释\context-inputs\test-coverage\test_coverage_report.json |

## Actions

- All readiness panels are clean; keep this dashboard with the release evidence.
- All audit checks passed; keep the audit with the model card as release evidence.
- Release evidence is complete; keep this bundle with the tagged version.
- Keep v445 context carryover evidence with the tagged version.

## Evidence

- `d\445\解释\context-inputs\registry\registry.json`: yes, JSON, 930 B
- `d\445\解释\context-inputs\registry\registry.csv`: yes, CSV, 48 B
- `d\445\解释\context-inputs\registry\registry.svg`: yes, SVG, 78 B
- `d\445\解释\context-inputs\registry\registry.html`: yes, HTML, 41 B
- `d\445\解释\context-inputs\model-card\model_card.json`: yes, JSON, 933 B
- `d\445\解释\context-inputs\model-card\model_card.md`: yes, MD, 19 B
- `d\445\解释\context-inputs\model-card\model_card.html`: yes, HTML, 43 B
- `d\445\解释\project-audit\project_audit.json`: yes, JSON, 13.5 KB
- `d\445\解释\project-audit\project_audit.md`: yes, MD, 3.6 KB
- `d\445\解释\project-audit\project_audit.html`: yes, HTML, 7.8 KB
- `d\445\解释\context-inputs\request-history-summary\request_history_summary.json`: yes, JSON, 441 B
- `d\445\解释\context-inputs\request-history-summary\request_history_summary.md`: yes, MD, 24 B
- `d\445\解释\context-inputs\request-history-summary\request_history_summary.html`: yes, HTML, 48 B
- `d\445\解释\context-inputs\benchmark-history\benchmark_history.json`: yes, JSON, 1.4 KB
- `d\445\解释\context-inputs\benchmark-history\benchmark_history.md`: yes, MD, 26 B
- `d\445\解释\context-inputs\benchmark-history\benchmark_history.html`: yes, HTML, 50 B
- `d\445\解释\ci-workflow-hygiene\ci_workflow_hygiene.json`: yes, JSON, 13.5 KB
- `d\445\解释\ci-workflow-hygiene\ci_workflow_hygiene.md`: yes, MD, 6.9 KB
- `d\445\解释\ci-workflow-hygiene\ci_workflow_hygiene.html`: yes, HTML, 9.6 KB
- `d\445\解释\context-inputs\test-coverage\test_coverage_report.json`: yes, JSON, 400 B
- `d\445\解释\context-inputs\test-coverage\test_coverage_report.md`: yes, MD, 22 B
- `d\445\解释\context-inputs\test-coverage\test_coverage_report.html`: yes, HTML, 46 B

# MiniGPT project audit

- Generated: `2026-05-26T11:40:12Z`
- Registry: `d\445\解释\context-inputs\registry\registry.json`
- Model card: `d\445\解释\context-inputs\model-card\model_card.json`
- Request history summary: `d\445\解释\context-inputs\request-history-summary\request_history_summary.json`
- Benchmark history: `d\445\解释\context-inputs\benchmark-history\benchmark_history.json`
- CI workflow hygiene: `d\445\解释\ci-workflow-hygiene\ci_workflow_hygiene.json`
- Test coverage report: `d\445\解释\context-inputs\test-coverage\test_coverage_report.json`

## Summary

| Field | Value |
| --- | --- |
| Overall status | pass |
| Score | 100 |
| Runs | 1 |
| Best run | v445-context-candidate |
| Ready runs | 1 |
| Request history status | pass |
| Request history records | 4 |
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
| Test coverage status | pass |
| Test coverage percent | 90.17 |
| Test coverage fail under | 80 |
| Test coverage gap | 0 |
| Pass checks | 17 |
| Warn checks | 0 |
| Fail checks | 0 |

## Checks

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

## Recommendations

- All audit checks passed; keep the audit with the model card as release evidence.

## Runs

| Rank | Run | Status | Best Val | Quality | Eval | Gen Quality | Card |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #1 | v445-context-candidate | ready | 0.8 | pass | 3 | pass (3 cases) | yes |

# MiniGPT release gate

- Release: `v445-context-carryover`
- Generated: `2026-05-26T11:42:32Z`
- Bundle: `d\445\解释\release-bundle\release_bundle.json`

## Summary

| Field | Value |
| --- | --- |
| Gate status | pass |
| Decision | approved |
| Release status | release-ready |
| Audit status | pass |
| Audit score | 100 |
| Ready runs | 1 |
| Missing artifacts | 0 |
| Test coverage status | pass |
| Test coverage percent | 90.17 |
| Test coverage fail under | 80 |
| Test coverage gap | 0 |
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
| Pass checks | 14 |
| Warn checks | 0 |
| Fail checks | 0 |

## Policy

| Field | Value |
| --- | --- |
| policy_profile | standard |
| profile_description | Default tagged-release policy that preserves the v30 gate behavior. |
| required_release_status | release-ready |
| required_audit_status | pass |
| minimum_audit_score | 90 |
| minimum_ready_runs | 1 |
| require_all_evidence_artifacts | True |
| require_generation_quality_audit_checks | True |
| require_request_history_summary_audit_check | True |
| require_benchmark_history_gate_check | True |
| require_test_coverage_audit_check | True |
| overrides | {"minimum_audit_score": false, "minimum_ready_runs": false, "require_benchmark_history": false, "require_generation_quality": false, "require_request_history_summary": false, "require_test_coverage": false} |

## Checks

| Status | Check | Detail |
| --- | --- | --- |
| pass | Release bundle schema is present | schema_version=1 |
| pass | Release status is ready | release_status=release-ready; required=release-ready. |
| pass | Audit status passed | audit_status=pass; required=pass. |
| pass | Audit score meets threshold | audit_score=100%; minimum=90%. |
| pass | Ready run count meets threshold | ready_runs=1; minimum=1. |
| pass | Best run is identified | best_run=v445-context-candidate. |
| pass | Evidence artifacts are complete | missing_artifacts=0; all evidence artifacts should exist. |
| pass | Top runs are listed | top_runs=1. |
| pass | Audit checks are clean | pass=17. |
| pass | Generation quality audit checks passed | generation_quality=pass, non_pass_generation_quality=pass. |
| pass | Request history summary audit check passed | request_history_summary=pass. |
| pass | Benchmark history release evidence passed | benchmark_history=pass; summary_status=pass; entries=1; ready=1; review=0; blocked=0; case_regressions=0; generation_flag_regressions=0; suite_design_not_ready=0; design_comparison_changed=0; readiness_requirement=pass; readiness_exit=0; readiness_failed_reasons=none; model_quality_claim=candidate_evidence; latest_boundary=standard-benchmark-candidate-evidence. |
| pass | Test coverage audit check passed | test_coverage_report=pass. |
| pass | Bundle has no warnings | warnings=0. |

## Recommendations

- Release gate passed; keep gate_report outputs with the tagged version.

## Bundle Recommendations

- Release evidence is complete; keep this bundle with the tagged version.
- All audit checks passed; keep the audit with the model card as release evidence.
- Keep v445 context carryover evidence with the tagged version.

# MiniGPT release readiness comparison

- Generated: `2026-05-27T09:13:29Z`
- Baseline: `D:\aiproj\d\462\解释\source-inputs\v461-baseline-receipt-ready\release_readiness.json`

## Summary

| Field | Value |
| --- | --- |
| Readiness reports | 2 |
| Baseline status | ready |
| Ready count | 2 |
| Blocked count | 0 |
| Improved count | 0 |
| Regressed count | 0 |
| Changed panel deltas | 0 |
| CI workflow regressions | 1 |
| CI order regressions | 0 |
| CI drift-contract smoke ready changes | 0 |
| CI drift-contract smoke ready regressions | 0 |
| CI tiny plan digest regressions | 0 |
| CI boundary gate check regressions | 0 |
| CI boundary plan check regressions | 0 |
| CI receipt plan-check changes | 1 |
| CI receipt plan-check regressions | 1 |
| CI workflow regression reasons | receipt_failure_smoke_plan_check_not_ready:1 |
| Max CI order violation delta | 0 |
| Test coverage regressions | 0 |
| Benchmark history deltas | 0 |
| Benchmark history regressions | 0 |
| Benchmark suite-design not-ready deltas | 0 |
| Benchmark suite-design not-ready regressions | 0 |
| Benchmark design-comparison change deltas | 0 |
| Benchmark readiness failed reasons added | 0 |
| Benchmark readiness failed reasons removed | 0 |
| Benchmark readiness failed reason removals | none |
| Benchmark readiness failed reason recovery deltas | 0 |
| Benchmark readiness failed reason mixed deltas | 0 |
| Benchmark readiness failed reason drift | stable:1 |

## Readiness Matrix

| Release | Status | Decision | Gate | Audit | Score | CI workflow | CI failed | CI order violations | CI plan digest | CI boundary gate | CI boundary plan | CI receipt plan | CI drift smoke ready | Request history | Coverage | Coverage % | Coverage gap | Benchmark history | Benchmark ready | Suite-design not-ready | Design changes | Benchmark readiness | Benchmark readiness exit | Benchmark regressions | Benchmark boundary | Maturity | Fail panels | Warn panels |
| --- | --- | --- | --- | --- | ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | --- | --- | ---: | ---: |
| v461-baseline-receipt-ready | ready | ship | pass | pass | 100 | pass | 0 | 0 | True | True | True | True | True | pass | pass | 90.17 | 0 | pass | 1 | 0 | 0 | pass | 0 | 0 | standard-benchmark-candidate-evidence | pass | 0 | 0 |
| v462-current-receipt-plan-regressed | ready | ship | pass | pass | 100 | pass | 0 | 0 | True | True | True | False | True | pass | pass | 90.17 | 0 | pass | 1 | 0 | 0 | pass | 0 | 0 | standard-benchmark-candidate-evidence | pass | 0 | 0 |

## Deltas

| Compared | Status delta | CI order violation delta | CI plan digest regressed | CI boundary gate regressed | CI boundary plan regressed | CI receipt plan changed | CI receipt plan regressed | CI drift smoke changed | CI drift smoke regressed | CI regression reasons | Coverage % delta | Coverage gap delta | Benchmark status delta | Suite-design not-ready delta | Design changes delta | Benchmark readiness changed | Benchmark readiness exit delta | Failed reason drift | Failed reasons added | Failed reasons removed | Benchmark case regression delta | Benchmark boundary changed | Panel changes | Explanation |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | --- | --- | ---: | --- | --- | --- |
| v462-current-receipt-plan-regressed | 0 | 0 | False | False | False | True | True | False | False | receipt_failure_smoke_plan_check_not_ready | 0 | 0 | 0 | 0 | 0 | False | 0 | stable |  |  | 0 | False |  | v462-current-receipt-plan-regressed moves from ready to ready (0). CI workflow promoted seed receipt failure-smoke plan check ready changed from True to False. CI workflow regression reason(s): receipt failure-smoke plan check readiness. No readiness status or panel delta is present. |

## Recommendations

- At least one readiness comparison shows CI workflow hygiene regression (receipt failure-smoke plan check readiness=1); inspect CI status deltas, failed-check deltas, order-violation deltas, and drift-smoke readiness deltas before release handoff.

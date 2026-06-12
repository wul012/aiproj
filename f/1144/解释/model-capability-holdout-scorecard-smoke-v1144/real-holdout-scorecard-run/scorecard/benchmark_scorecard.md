# MiniGPT benchmark scorecard

- Generated: `2026-06-12T10:48:11Z`
- Run dir: `f\1144\解释\model-capability-holdout-scorecard-smoke-v1144\real-holdout-scorecard-run`
- Registry: `missing`

## Summary

| Key | Value |
| --- | --- |
| Overall status | pass |
| Overall score | 97.0 |
| Eval cases | 5 |
| Eval coverage | pass |
| Eval comparison | pass |
| Suite design coverage |  |
| Suite design comparison |  |
| Suite design duplicate seeds |  |
| Generation quality | pass |
| Generation flags | 0 |
| Dominant generation flag |  |
| Worst generation case |  |
| Rubric correctness | pass |
| Rubric average | 100.0 |
| Weakest rubric case | holdout-scorecard-continuation-hard |
| Pair batch cases | 5 |
| Pair generated differences | 0 |
| Pair comparison mode | same_checkpoint_baseline |
| Task type groups | 3 |
| Weakest task type | continuation |
| Difficulty groups | 3 |
| Weakest difficulty | medium |

## Components

| Component | Status | Score | Weight | Detail |
| --- | --- | ---: | ---: | --- |
| Eval Suite Coverage | pass | 100.0 | 0.15 | 5 fixed prompt case(s). coverage=pass, comparison=pass. |
| Generation Quality | pass | 100.0 | 0.2 | 5 pass / 0 warn / 0 fail. |
| Rubric Correctness | pass | 100.0 | 0.25 | 5 pass / 0 warn / 0 fail. |
| Pair Consistency | pass | 90.0 | 0.15 | 5 / 5 pair generations matched exactly. Same-checkpoint baseline proves reproducibility, not cross-checkpoint improvement. |
| Pair Delta Stability | pass | 90.0 | 0.15 | avg abs generated delta=0, max abs generated delta=0. Same-checkpoint delta is a reproducibility baseline. |
| Benchmark Evidence Completeness | pass | 100.0 | 0.1 | 3 / 3 evidence groups present. |

## Task Type Drilldown

| Group | Status | Score | Cases |
| --- | --- | ---: | ---: |
| qa | pass | 100.0 | 2 |
| summary | pass | 100.0 | 2 |
| continuation | pass | 95.0 | 1 |

## Difficulty Drilldown

| Group | Status | Score | Cases |
| --- | --- | ---: | ---: |
| easy | pass | 100.0 | 2 |
| hard | pass | 100.0 | 2 |
| medium | pass | 95.0 | 1 |

## Rubric Scores

| Case | Status | Score | Missing Terms |
| --- | --- | ---: | --- |
| holdout-scorecard-continuation-hard | pass | 100.0 | [] |
| holdout-scorecard-qa-easy | pass | 100.0 | [] |
| holdout-scorecard-qa-hard | pass | 100.0 | [] |
| holdout-scorecard-summary-easy | pass | 100.0 | [] |
| holdout-scorecard-summary-medium | pass | 100.0 | [] |

## Case Scores

| Case | Task | Eval chars | Gen status | Rubric | Pair delta | Pair equal |
| --- | --- | ---: | --- | ---: | ---: | --- |
| holdout-scorecard-continuation-hard | continuation | 11 | pass | 100.0 | 0 | True |
| holdout-scorecard-qa-easy | qa | 11 | pass | 100.0 | 0 | True |
| holdout-scorecard-qa-hard | qa | 11 | pass | 100.0 | 0 | True |
| holdout-scorecard-summary-easy | summary | 11 | pass | 100.0 | 0 | True |
| holdout-scorecard-summary-medium | summary | 11 | pass | 100.0 | 0 | True |

## Recommendations

- Use this scorecard as the single benchmark entry point for the current run.
- Review weakest rubric case `holdout-scorecard-continuation-hard` at score 100.0 before trusting benchmark gains.
- Run a different candidate checkpoint pair before using pair metrics as model improvement evidence.
- Review weakest task type `continuation` at score 95.0 before expanding the suite.
- Review weakest difficulty `medium` at score 95.0 before comparing runs.
- Next step: compare rubric score changes across runs so correctness regressions are visible in the registry.

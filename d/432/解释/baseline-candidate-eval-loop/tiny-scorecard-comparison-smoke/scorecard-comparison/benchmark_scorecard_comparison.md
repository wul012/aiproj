# MiniGPT tiny scorecard comparison smoke

- Generated: `2026-05-25T15:28:41Z`
- Scorecards: `2`
- Baseline: `tiny-baseline`
- Best overall: `tiny-candidate`
- Best rubric: `tiny-candidate`

## Summary

| Field | Value |
| --- | --- |
| Improved overall | 0 |
| Regressed overall | 0 |
| Improved rubric | 0 |
| Regressed rubric | 0 |
| Generation flag improvements | 0 |
| Generation flag regressions | 0 |
| Baseline dominant generation flag | missing |
| Baseline eval comparison | pass |
| Baseline design comparison | pass |
| Non comparison-ready runs | none |
| Non design-ready runs | none |
| Case regressions | 0 |
| Case improvements | 0 |
| Weakest regression case | missing |

## Runs

| Run | Overall | Rubric | Eval Compare | Design Compare | Gen Flags | Dominant Flag | Case Count | Weakest Case | Relation | Explanation |
| --- | ---: | ---: | --- | --- | ---: | --- | ---: | --- | --- | --- |
| tiny-baseline | 81.17 (+0) | 36.67 (+0) | pass | pass | 0 (+0) | missing | 10 | continuation-science:35 | baseline | This run is the baseline for scorecard deltas. |
| tiny-candidate | 81.17 (+0) | 36.67 (+0) | pass | pass | 0 (+0) | missing | 10 | continuation-science:35 | tied | Overall score changed +0 from tiny-baseline. Rubric average changed +0. Generation-quality flags changed +0. |

## Case Deltas

| Case | Run | Task | Rubric Delta | Relation | Missing Terms Delta | Failed Checks Delta | Explanation |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| classification-risk-level | tiny-baseline | classification/medium | +0 | baseline | none | none | Baseline case row. |
| comparison-baseline | tiny-baseline | comparison/hard | +0 | baseline | none | none | Baseline case row. |
| continuation-science | tiny-baseline | continuation/easy | +0 | baseline | none | none | Baseline case row. |
| factual-val-loss | tiny-baseline | factual-consistency/medium | +0 | baseline | none | none | Baseline case row. |
| qa-training-loop | tiny-baseline | qa/medium | +0 | baseline | none | none | Baseline case row. |
| refusal-boundary | tiny-baseline | safety-boundary/hard | +0 | baseline | none | none | Baseline case row. |
| self-check-missing-data | tiny-baseline | self-check/hard | +0 | baseline | none | none | Baseline case row. |
| structured-experiment-json | tiny-baseline | structured/medium | +0 | baseline | none | none | Baseline case row. |
| style-rewrite-concise | tiny-baseline | rewrite/easy | +0 | baseline | none | none | Baseline case row. |
| summary-evidence-chain | tiny-baseline | summary/medium | +0 | baseline | none | none | Baseline case row. |
| classification-risk-level | tiny-candidate | classification/medium | +0 | tied | none | none | Rubric score changed +0. |
| comparison-baseline | tiny-candidate | comparison/hard | +0 | tied | none | none | Rubric score changed +0. |
| continuation-science | tiny-candidate | continuation/easy | +0 | tied | none | none | Rubric score changed +0. |
| factual-val-loss | tiny-candidate | factual-consistency/medium | +0 | tied | none | none | Rubric score changed +0. |
| qa-training-loop | tiny-candidate | qa/medium | +0 | tied | none | none | Rubric score changed +0. |
| refusal-boundary | tiny-candidate | safety-boundary/hard | +0 | tied | none | none | Rubric score changed +0. |
| self-check-missing-data | tiny-candidate | self-check/hard | +0 | tied | none | none | Rubric score changed +0. |
| structured-experiment-json | tiny-candidate | structured/medium | +0 | tied | none | none | Rubric score changed +0. |
| style-rewrite-concise | tiny-candidate | rewrite/easy | +0 | tied | none | none | Rubric score changed +0. |
| summary-evidence-chain | tiny-candidate | summary/medium | +0 | tied | none | none | Rubric score changed +0. |

## Task Type Deltas

| Group | Run | Score Delta | Rubric Delta | Relation | Explanation |
| --- | --- | ---: | ---: | --- | --- |
| classification | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| comparison | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| continuation | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| factual-consistency | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| qa | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| rewrite | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| safety-boundary | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| self-check | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| structured | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| summary | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| classification | tiny-candidate | +0 | +0 | tied | task_type `classification` score changed +0. Rubric changed +0. |
| comparison | tiny-candidate | +0 | +0 | tied | task_type `comparison` score changed +0. Rubric changed +0. |
| continuation | tiny-candidate | +0 | +0 | tied | task_type `continuation` score changed +0. Rubric changed +0. |
| factual-consistency | tiny-candidate | +0 | +0 | tied | task_type `factual-consistency` score changed +0. Rubric changed +0. |
| qa | tiny-candidate | +0 | +0 | tied | task_type `qa` score changed +0. Rubric changed +0. |
| rewrite | tiny-candidate | +0 | +0 | tied | task_type `rewrite` score changed +0. Rubric changed +0. |
| safety-boundary | tiny-candidate | +0 | +0 | tied | task_type `safety-boundary` score changed +0. Rubric changed +0. |
| self-check | tiny-candidate | +0 | +0 | tied | task_type `self-check` score changed +0. Rubric changed +0. |
| structured | tiny-candidate | +0 | +0 | tied | task_type `structured` score changed +0. Rubric changed +0. |
| summary | tiny-candidate | +0 | +0 | tied | task_type `summary` score changed +0. Rubric changed +0. |

## Difficulty Deltas

| Group | Run | Score Delta | Rubric Delta | Relation | Explanation |
| --- | --- | ---: | ---: | --- | --- |
| easy | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| hard | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| medium | tiny-baseline | +0 | +0 | baseline | Baseline group row. |
| easy | tiny-candidate | +0 | +0 | tied | difficulty `easy` score changed +0. Rubric changed +0. |
| hard | tiny-candidate | +0 | +0 | tied | difficulty `hard` score changed +0. Rubric changed +0. |
| medium | tiny-candidate | +0 | +0 | tied | difficulty `medium` score changed +0. Rubric changed +0. |

## Recommendations

- No rubric average change was detected; use case-level rows to check whether individual prompts moved in opposite directions.

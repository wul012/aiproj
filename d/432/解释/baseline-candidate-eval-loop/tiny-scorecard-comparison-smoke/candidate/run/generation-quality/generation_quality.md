# MiniGPT generation quality report

- Generated: `2026-05-25T15:28:38Z`
- Source: `d\432\解释\baseline-candidate-eval-loop\tiny-scorecard-comparison-smoke\candidate\run\eval_suite\eval_suite.json`
- Source type: `eval_suite`

## Summary

| Field | Value |
| --- | --- |
| Overall status | pass |
| Cases | 10 |
| Pass | 10 |
| Warn | 0 |
| Fail | 0 |
| Avg chars | 3 |
| Avg unique ratio | 1 |
| Avg repeated ngram ratio | 0 |
| Max repeat run | 1 |

## Flag Breakdown

| Field | Value |
| --- | --- |
| Total flags | 0 |
| Fail flags | 0 |
| Warn flags | 0 |

| Flag id | Count |
| --- | --- |
| none | 0 |

| Status | Case | Flag Count | Flag ids |
| --- | --- | --- | --- |
| pass | none | 0 | none |

## Policy

| Field | Value |
| --- | --- |
| min_continuation_chars | 1 |
| min_unique_ratio | 0.25 |
| max_repeat_run | 8 |
| max_repeated_ngram_ratio | 0.65 |
| ngram_size | 2 |

## Cases

| Status | Case | Chars | Unique Ratio | Repeated Ngram | Repeat Run | Flags |
| --- | --- | --- | --- | --- | --- | --- |
| pass | continuation-science | 3 | 100.0% | 0.0% | 1 | none |
| pass | qa-training-loop | 3 | 100.0% | 0.0% | 1 | none |
| pass | summary-evidence-chain | 3 | 100.0% | 0.0% | 1 | none |
| pass | structured-experiment-json | 3 | 100.0% | 0.0% | 1 | none |
| pass | factual-val-loss | 3 | 100.0% | 0.0% | 1 | none |
| pass | classification-risk-level | 3 | 100.0% | 0.0% | 1 | none |
| pass | style-rewrite-concise | 3 | 100.0% | 0.0% | 1 | none |
| pass | refusal-boundary | 3 | 100.0% | 0.0% | 1 | none |
| pass | self-check-missing-data | 3 | 100.0% | 0.0% | 1 | none |
| pass | comparison-baseline | 3 | 100.0% | 0.0% | 1 | none |

## Recommendations

- Generation quality checks passed; keep this report with eval artifacts.

# MiniGPT generation quality report

- Generated: `2026-05-28T23:45:26Z`
- Source: `e\478\解释\model-capability-token-budget-stability\seeds\seed-1337\token-cap-4\ladder\rungs\max-iters-4\run\eval_suite\eval_suite.json`
- Source type: `eval_suite`

## Summary

| Field | Value |
| --- | --- |
| Overall status | pass |
| Cases | 10 |
| Pass | 10 |
| Warn | 0 |
| Fail | 0 |
| Avg chars | 4 |
| Avg unique ratio | 0.8917 |
| Avg repeated ngram ratio | 0 |
| Max repeat run | 2 |

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
| pass | continuation-science | 4 | 100.0% | 0.0% | 1 | none |
| pass | qa-training-loop | 4 | 100.0% | 0.0% | 1 | none |
| pass | summary-evidence-chain | 4 | 75.0% | 0.0% | 2 | none |
| pass | structured-experiment-json | 4 | 100.0% | 0.0% | 1 | none |
| pass | factual-val-loss | 4 | 75.0% | 0.0% | 1 | none |
| pass | classification-risk-level | 4 | 66.7% | 0.0% | 2 | none |
| pass | style-rewrite-concise | 4 | 75.0% | 0.0% | 2 | none |
| pass | refusal-boundary | 4 | 100.0% | 0.0% | 1 | none |
| pass | self-check-missing-data | 4 | 100.0% | 0.0% | 1 | none |
| pass | comparison-baseline | 4 | 100.0% | 0.0% | 1 | none |

## Recommendations

- Generation quality checks passed; keep this report with eval artifacts.

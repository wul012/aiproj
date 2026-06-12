# MiniGPT required term coverage real execution v1143

- Generated: `2026-06-12T09:09:08Z`
- Status: `pass`
- Decision: `model_capability_required_term_real_execution_ready`

## Summary

| Metric | Value |
| --- | --- |
| required_term_real_execution_ready | True |
| suite_id | capability-regression-01 |
| check_id | required_term_coverage |
| source_execution_mode | reuse_existing_evidence_paths |
| case_count | 1 |
| executed_case_count | 1 |
| passed_case_count | 1 |
| failed_case_count | 0 |
| required_terms | fixed, loss |
| hit_terms | fixed, loss |
| missed_terms |  |
| model_quality_claim | single_check_real_execution |
| promotion_ready | False |
| next_step | run_real_holdout_scorecard_smoke_v1144 |
| failed_check_count | 0 |

## Required Term Real Generation

| suite_id | check_id | case_id | prompt | continuation | required_terms | hit_terms | missed_terms | case_pass | checkpoint | tokenizer | generation_error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| capability-regression-01 | required_term_coverage | capability-regression-01-required-term-coverage-real-execution | answer with exactly two words: fixed loss answer: |  fixed loss | fixed, loss | fixed, loss |  | True | f\1143\解释\model-capability-required-term-real-execution-v1143\tiny-required-term-checkpoint\checkpoint.pt | f\1143\解释\model-capability-required-term-real-execution-v1143\tiny-required-term-checkpoint\tokenizer.json |  |

## Recommendations

- Treat v1143 as one bounded real generation check, not as a promotion decision.
- Use v1144 to stand up the real holdout scorecard smoke after this first generation anchor.

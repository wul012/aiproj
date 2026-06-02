# MiniGPT Required-Term Pair-Readiness Corpus Materialization

- Status: `pass`
- Decision: `pair_readiness_corpus_materialized`
- Training corpus: `e\715\解释\model-capability-required-term-pair-readiness-structured-template-corpus-materialization\pair_readiness_training_corpus.txt`
- Heldout eval fixture: `e\715\解释\model-capability-required-term-pair-readiness-structured-template-corpus-materialization\pair_readiness_heldout_eval_fixture.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| contract_passed | pass | pass | source contract must pass |
| contract_decision | pass | pair_readiness_structured_template_contract_ready | materialization requires a ready pair-readiness contract |
| repeat_positive | pass | 320 | repeat must be positive |
| training_rows_present | pass | 14 | training rows must be present |
| heldout_not_in_training_rows | pass | False | heldout pair probe must not be a training row |
| heldout_not_in_corpus | pass | False | heldout pair probe must not appear as a corpus line |

# MiniGPT randomized holdout acceptance summary

- Status: `pass`
- Decision: `randomized_holdout_acceptance_summary_ready`
- Ready: `True`
- Bounded accepted: `True`
- Promotion: `False`
- Cases: `20`
- Seed: `914`
- Allowed use: `bounded_model_capability_governance_only`
- Next step: `check_randomized_holdout_acceptance_summary_contract`

## Accepted Claims

| Claim | Status | Scope | Claim text | Cases | Seed | Allowed use |
| --- | --- | --- | --- | --- | --- | --- |
| bounded_randomized_target_hidden_holdout_claim | accepted | randomized_target_hidden_20_case_tiny_checkpoint_only | bounded_randomized_target_hidden_holdout_claim_only | 20 | 914 | bounded_model_capability_governance_only |

## Blocked Claims

| Claim | Status | Reason |
| --- | --- | --- |
| production_promotion | blocked | promotion_ready remains false |
| general_model_quality | blocked | evidence is limited to a 20-case tiny-checkpoint randomized holdout |
| larger_corpus_transfer | blocked | no larger corpus or external benchmark evidence is attached |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| decision_index_file_exists | pass | e\922\解释\randomized-holdout-decision-index\randomized_holdout_decision_index.json | source decision index file must exist |
| decision_index_passed | pass | pass | decision index must pass |
| decision_index_ready | pass | randomized_holdout_decision_index_ready | decision index must be ready |
| summary_ready | pass | True | index summary must be ready |
| bounded_acceptance_true | pass | True | bounded randomized holdout claim must be accepted |
| promotion_still_false | pass | False | acceptance summary must not become direct promotion |
| approved_for_promotion_false | pass | False | direct promotion approval must remain false |
| candidate_count_floor | pass | 20 | acceptance summary requires the randomized 20-case floor |
| seed_present | pass | 914 | acceptance summary must carry the randomized seed |
| pass_rate_complete | pass | 1.0 | acceptance summary requires complete randomized replay pass rate |
| claim_scope_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | accepted claim must remain bounded |
| source_rows_present | pass | 4 | summary must retain source rows |
| source_kinds_complete | pass | ['bounded_decision', 'bounded_gate', 'candidate_packet', 'candidate_packet_review'] | source rows must include packet, review, gate, and decision |
| source_rows_ready | pass | [True, True, True, True] | all source rows must remain passed and ready |
| source_rows_block_promotion | pass | [False, False, False, False] | all source rows must keep promotion false |

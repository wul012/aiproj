# MiniGPT randomized holdout publication decision index

- Status: `pass`
- Decision: `randomized_holdout_publication_decision_index_ready`
- Index ready: `True`
- Indexed decision: `accept_bounded_randomized_holdout_publication`
- Bounded accepted: `True`
- Promotion: `False`
- Accepted claims: `1`
- Blocked claims: `3`
- Candidate cases: `20`
- Random seed: `914`
- Pass rate: `1.0`
- Allowed use: `bounded_model_capability_governance_only`
- Claim: `bounded_randomized_target_hidden_holdout_claim_only`
- Next step: `build_randomized_holdout_publication_registry_entry`

## Source Rows

| Kind | Exists | Status | Ready | Accepted | Blocked | Cases | Seed | Use | Next | Path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| publication_decision | True | pass | True | 1 | 3 | 20 | 914 | bounded_model_capability_governance_only | index_randomized_holdout_publication_decision | e\927\解释\randomized-holdout-publication-decision\randomized_holdout_publication_decision.json |
| publication_review | True | pass | True | 1 | 3 | 20 | 914 | bounded_model_capability_governance_only | record_randomized_holdout_publication_decision | e\926\解释\randomized-holdout-acceptance-publication-packet-review\randomized_holdout_acceptance_publication_packet_review.json |
| publication_packet | True | pass | True | 1 | 3 | 20 | 914 | bounded_model_capability_governance_only | review_randomized_holdout_acceptance_publication_packet | e\925\解释\randomized-holdout-acceptance-publication-packet\randomized_holdout_acceptance_publication_packet.json |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_files_exist | pass | [True, True, True] | all indexed publication-chain source files must exist |
| decision_passed | pass | pass | publication decision must pass |
| decision_accepted | pass | randomized_holdout_publication_decision_accepted | publication decision must be accepted |
| decision_ready | pass | True | publication decision summary must be ready |
| decision_accepts_bounded_publication | pass | True | publication decision must accept only bounded publication |
| review_passed | pass | pass | publication review must pass |
| review_ready | pass | True | publication review summary must be ready |
| review_approved_publication | pass | True | publication review must approve bounded publication |
| packet_passed | pass | pass | publication packet must pass |
| packet_ready | pass | True | publication packet summary must be ready |
| accepted_counts_match | pass | [1, 1, 1] | accepted claim counts must match exactly one |
| blocked_counts_match | pass | [3, 3, 3] | blocked claim counts must match and preserve at least three boundaries |
| candidate_counts_match | pass | [20, 20, 20] | candidate case counts must match the randomized holdout floor |
| random_seed_matches | pass | [914, 914, 914] | all sources must preserve the same randomized seed |
| pass_rate_complete | pass | [1.0, 1.0, 1.0] | all sources must preserve complete randomized replay pass rate |
| allowed_use_bounded | pass | ['bounded_model_capability_governance_only', 'bounded_model_capability_governance_only', 'bounded_model_capability_governance_only'] | all sources must keep bounded governance allowed use |
| model_quality_claim_bounded | pass | ['bounded_randomized_target_hidden_holdout_claim_only', 'bounded_randomized_target_hidden_holdout_claim_only', 'bounded_randomized_target_hidden_holdout_claim_only'] | all sources must keep the bounded randomized holdout claim |
| promotion_still_false | pass | [False, False, False] | publication index must not widen into direct promotion |
| approved_for_promotion_false | pass | [False, False, False] | direct promotion approval must remain false |
| source_checks_clean | pass | [0, 0, 0] | all indexed source summaries must have clean checks |
| next_steps_aligned | pass | ['index_randomized_holdout_publication_decision', 'record_randomized_holdout_publication_decision', 'review_randomized_holdout_acceptance_publication_packet'] | source next-step routing must match packet -> review -> decision -> index |

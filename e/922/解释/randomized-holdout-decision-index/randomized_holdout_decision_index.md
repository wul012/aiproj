# MiniGPT randomized holdout decision index

- Status: `pass`
- Decision: `randomized_holdout_decision_index_ready`
- Index ready: `True`
- Indexed decision: `accept_bounded_randomized_holdout_claim`
- Bounded accepted: `True`
- Promotion: `False`
- Candidate cases: `20`
- Random seed: `914`
- Pass rate: `1.0`
- Claim: `bounded_randomized_target_hidden_holdout_claim_only`
- Next step: `build_randomized_holdout_acceptance_summary`

## Source Rows

| Kind | Exists | Status | Decision | Ready | Cases | Seed | Claim | Path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bounded_decision | True | pass | randomized_holdout_bounded_promotion_decision_accepted | True | 20 | 914 | bounded_randomized_target_hidden_holdout_claim_only | e\921\解释\randomized-holdout-bounded-promotion-decision\randomized_holdout_bounded_promotion_decision.json |
| bounded_gate | True | pass | randomized_holdout_bounded_promotion_gate_passed | True | 20 | 914 | bounded_gate_only | e\920\解释\randomized-holdout-bounded-promotion-gate\randomized_holdout_bounded_promotion_gate.json |
| candidate_packet_review | True | pass | randomized_holdout_candidate_promotion_packet_review_ready | True | 20 | 914 | candidate_packet_review_only | e\919\解释\randomized-holdout-candidate-promotion-packet-review\randomized_holdout_candidate_promotion_packet_review.json |
| candidate_packet | True | pass | randomized_holdout_candidate_promotion_packet_ready | True | 20 | 914 | candidate_packet_only | e\918\解释\randomized-holdout-candidate-promotion-packet\randomized_holdout_candidate_promotion_packet.json |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_files_exist | pass | [True, True, True, True] | all indexed source artifact files must exist |
| bounded_decision_passed | pass | pass | bounded decision must pass |
| bounded_decision_accepted | pass | randomized_holdout_bounded_promotion_decision_accepted | bounded decision must be accepted |
| bounded_decision_ready | pass | True | bounded decision summary must be ready |
| bounded_acceptance_true | pass | True | decision must accept bounded randomized holdout claim |
| gate_passed | pass | pass | bounded gate must pass |
| gate_ready | pass | True | bounded gate summary must be ready |
| gate_approves_decision | pass | True | gate must approve bounded decision entry |
| review_passed | pass | pass | candidate packet review must pass |
| review_ready | pass | True | candidate packet review summary must be ready |
| review_approves_gate | pass | True | review must approve bounded gate entry |
| packet_passed | pass | pass | candidate packet must pass |
| packet_ready | pass | True | candidate packet summary must be ready |
| packet_authorized | pass | True | candidate packet must be authorized |
| candidate_count_floor | pass | [20, 20, 20, 20] | all levels must keep at least the randomized 20-case floor |
| candidate_counts_match | pass | [20, 20, 20, 20] | decision, gate, review, and packet candidate counts must match |
| clean_counts_match_candidate_count | pass | [20, 20, 20] | gate, review, and packet clean randomized counts must match candidate count |
| random_seed_matches | pass | [914, 914, 914, 914] | all levels must carry the same randomized seed |
| pass_rate_complete | pass | [1.0, 1.0, 1.0, 1.0] | all levels must preserve the complete randomized replay pass rate |
| source_checks_clean | pass | [0, 0, 0, 0] | indexed source summaries must have no failed checks |
| promotion_still_false | pass | [False, False, False, False] | decision index must not widen into direct promotion |
| approved_for_promotion_false | pass | [False, False, False, False] | direct promotion approval must remain false |
| claim_scopes_expected | pass | ['bounded_randomized_target_hidden_holdout_claim_only', 'bounded_gate_only', 'candidate_packet_review_only', 'candidate_packet_only'] | each layer must keep its bounded claim scope |

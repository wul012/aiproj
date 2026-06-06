# MiniGPT randomized holdout bounded promotion decision

- Status: `pass`
- Decision: `randomized_holdout_bounded_promotion_decision_accepted`
- Final decision: `accept_bounded_randomized_holdout_claim`
- Bounded accepted: `True`
- Promotion: `False`
- Candidate cases: `20`
- Random seed: `914`
- Pass rate: `1.0`
- Claim scope: `randomized_target_hidden_20_case_tiny_checkpoint_only`
- Claim: `bounded_randomized_target_hidden_holdout_claim_only`
- Next step: `build_randomized_holdout_decision_index`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| gate_file_exists | pass | e\920\解释\randomized-holdout-bounded-promotion-gate\randomized_holdout_bounded_promotion_gate.json | bounded gate source file must exist |
| review_file_exists | pass | e\919\解释\randomized-holdout-candidate-promotion-packet-review\randomized_holdout_candidate_promotion_packet_review.json | candidate packet review source file must exist |
| packet_file_exists | pass | e\918\解释\randomized-holdout-candidate-promotion-packet\randomized_holdout_candidate_promotion_packet.json | candidate packet source file must exist |
| gate_passed | pass | pass | bounded gate must pass |
| gate_decision_passed | pass | randomized_holdout_bounded_promotion_gate_passed | bounded gate decision must pass |
| gate_ready | pass | {'summary': True, 'gate': True} | bounded gate must be ready |
| gate_allows_bounded_decision | pass | True | gate must approve bounded decision entry |
| gate_routes_to_decision | pass | record_randomized_holdout_bounded_promotion_decision | gate must route to bounded decision |
| review_passed | pass | pass | candidate packet review must pass |
| packet_passed | pass | pass | candidate packet must pass |
| candidate_count_floor | pass | {'gate': 20, 'review': 20, 'packet': 20} | bounded decision requires the randomized 20-case floor |
| candidate_counts_match | pass | {'gate': 20, 'review': 20, 'packet': 20} | gate, review, and packet candidate counts must match |
| random_seed_matches | pass | {'gate': 914, 'review': 914, 'packet': 914} | gate, review, and packet must carry the same seed |
| pass_rate_complete | pass | {'gate': 1.0, 'review': 1.0, 'packet': 1.0} | bounded decision requires a complete replay pass rate |
| clean_cases_match | pass | {'gate': 20, 'review': 20, 'packet': 20} | clean randomized case counts must match |
| source_checks_clean | pass | {'gate': 0, 'review': 0, 'packet': 0} | all upstream checks must be clean |
| promotion_still_false | pass | {'gate': False, 'review': False, 'packet': False} | bounded decision must not become production promotion |
| approved_for_promotion_false | pass | {'gate': False, 'review': False, 'packet': False} | direct promotion approval must stay false |
| claim_scopes_expected | pass | {'gate': 'bounded_gate_only', 'review': 'candidate_packet_review_only', 'packet': 'candidate_packet_only'} | claim scopes must stay bounded |

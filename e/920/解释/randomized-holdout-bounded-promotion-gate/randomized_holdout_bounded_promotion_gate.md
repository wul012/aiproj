# MiniGPT randomized holdout bounded promotion gate

- Status: `pass`
- Decision: `randomized_holdout_bounded_promotion_gate_passed`
- Gate ready: `True`
- Gate decision: `allow_bounded_randomized_holdout_promotion_decision`
- Candidate cases: `20`
- Random seed: `914`
- Pass rate: `1.0`
- Bounded decision: `True`
- Promotion: `False`
- Claim: `bounded_gate_only`
- Next step: `record_randomized_holdout_bounded_promotion_decision`

## Allowed Next Steps

- `record_randomized_holdout_bounded_promotion_decision`
- `build_randomized_holdout_decision_index`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| review_file_exists | pass | e\919\解释\randomized-holdout-candidate-promotion-packet-review\randomized_holdout_candidate_promotion_packet_review.json | candidate packet review source file must exist |
| packet_file_exists | pass | e\918\解释\randomized-holdout-candidate-promotion-packet\randomized_holdout_candidate_promotion_packet.json | candidate packet source file must exist |
| review_passed | pass | pass | candidate packet review must pass |
| review_decision_ready | pass | randomized_holdout_candidate_promotion_packet_review_ready | candidate packet review decision must be ready |
| review_summary_ready | pass | True | review summary must be ready |
| review_approves_bounded_gate | pass | True | review must approve bounded gate entry |
| review_routes_to_gate | pass | build_randomized_holdout_bounded_promotion_gate | review must route to this gate |
| packet_passed | pass | pass | candidate packet must pass |
| packet_ready | pass | {'summary': True, 'packet': True} | candidate packet must be ready |
| candidate_count_floor | pass | {'review': 20, 'packet': 20} | gate requires the randomized 20-case floor |
| candidate_counts_match | pass | {'review': 20, 'packet': 20} | review and packet candidate counts must match |
| random_seed_matches | pass | {'review': 914, 'packet': 914} | review and packet must carry the same randomized seed |
| pass_rate_complete | pass | {'review': 1.0, 'packet': 1.0} | gate requires a complete randomized replay pass rate |
| clean_cases_match | pass | {'review': 20, 'packet': 20} | clean randomized case counts must match candidate count |
| packet_negative_control_rejected | pass | 0 | gate requires the packet negative control to remain rejected |
| source_checks_clean | pass | {'review': 0, 'packet': 0} | review and packet checks must be clean |
| promotion_still_false | pass | {'review': False, 'packet_summary': False, 'packet': False} | bounded gate must not become direct promotion |
| approved_for_promotion_false | pass | {'review': False, 'packet_summary': False, 'packet': False} | direct promotion approval must stay false |
| claim_scope_bounded | pass | {'review': 'candidate_packet_review_only', 'packet': 'candidate_packet_only'} | claims must stay at packet-review and packet-only scope |

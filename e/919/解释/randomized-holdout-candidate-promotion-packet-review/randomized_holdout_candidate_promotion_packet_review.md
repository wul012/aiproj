# MiniGPT randomized holdout candidate promotion packet review

- Status: `pass`
- Decision: `randomized_holdout_candidate_promotion_packet_review_ready`
- Review ready: `True`
- Review decision: `accept_randomized_holdout_candidate_packet_for_bounded_gate`
- Candidate cases: `20`
- Random seed: `914`
- Pass rate: `1.0`
- Bounded gate: `True`
- Promotion: `False`
- Scope: `bounded_randomized_holdout_candidate_review_only`
- Next step: `build_randomized_holdout_bounded_promotion_gate`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| candidate_packet_passed | pass | pass | candidate packet must pass |
| candidate_packet_decision_ready | pass | randomized_holdout_candidate_promotion_packet_ready | candidate packet decision must be ready |
| candidate_packet_summary_ready | pass | True | candidate packet summary must be ready |
| packet_ready | pass | True | source packet body must be ready |
| handoff_ready_for_review | pass | ready_for_candidate_promotion_packet_review | candidate packet must route to packet review |
| candidate_case_count_floor | pass | 20 | review requires the randomized 20-case floor |
| suite_case_count_matches | pass | {'suite': 20, 'candidate': 20} | suite and candidate counts must match |
| clean_cases_complete | pass | 20 | all candidate prompts must remain clean randomized prompts |
| random_seed_present | pass | 914 | review needs the randomized source seed |
| pass_rate_complete | pass | 1.0 | candidate packet must preserve the 1.0 randomized replay pass rate |
| negative_control_rejected | pass | 0 | dry-run negative control must remain rejected |
| candidate_packet_authorized | pass | True | source review must authorize the candidate packet |
| source_checks_clean | pass | 0 | source packet checks must be clean |
| evidence_count | pass | 4 | review requires suite, dry-run, real replay, and replay review evidence |
| evidence_files_exist | pass | [{'kind': 'randomized_replay_review', 'path': 'e\\917\\解释\\randomized-target-hidden-holdout-replay-review\\randomized_target_hidden_holdout_replay_review.json', 'exists': True, 'status': 'pass', 'decision': 'randomized_target_hidden_holdout_replay_review_clean_signal_candidate_packet_required', 'ready_key': 'randomized_target_hidden_holdout_replay_review_ready', 'ready_value': True, 'promotion_ready': False, 'role': 'authorizes candidate packet while blocking direct promotion'}, {'kind': 'randomized_real_replay', 'path': 'e\\916\\解释\\randomized-target-hidden-holdout-real-replay\\randomized_target_hidden_holdout_real_replay.json', 'exists': True, 'status': 'pass', 'decision': 'randomized_target_hidden_holdout_real_replay_passed_review_required', 'ready_key': 'randomized_target_hidden_holdout_real_replay_ready', 'ready_value': True, 'promotion_ready': False, 'role': 'proves the real checkpoint passes randomized target-hidden prompts'}, {'kind': 'randomized_dry_run', 'path': 'e\\915\\解释\\randomized-target-hidden-holdout-dry-run\\randomized_target_hidden_holdout_dry_run.json', 'exists': True, 'status': 'pass', 'decision': 'randomized_target_hidden_holdout_dry_run_passed', 'ready_key': 'randomized_target_hidden_holdout_dry_run_ready', 'ready_value': True, 'promotion_ready': False, 'role': 'proves the scoring contract rejects the fixed-only negative control'}, {'kind': 'randomized_suite', 'path': 'e\\914\\解释\\randomized-target-hidden-holdout-suite\\randomized_target_hidden_holdout_suite.json', 'exists': True, 'status': 'pass', 'decision': 'randomized_target_hidden_holdout_suite_ready', 'ready_key': 'randomized_target_hidden_holdout_suite_ready', 'ready_value': True, 'promotion_ready': False, 'role': 'defines the 20 target-hidden randomized prompts'}] | all evidence source paths must exist |
| evidence_ready | pass | [True, True, True, True] | all evidence rows must report ready |
| evidence_keeps_promotion_false | pass | [False, False, False, False] | source evidence must not claim promotion |
| packet_keeps_promotion_false | pass | {'summary': False, 'packet': False} | candidate packet review must not widen into promotion |
| approved_for_promotion_false | pass | {'summary': False, 'packet': False} | direct promotion must remain false |
| claim_is_candidate_packet_only | pass | candidate_packet_only | source claim must remain candidate-packet only |

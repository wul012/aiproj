# MiniGPT randomized holdout candidate promotion packet

- Status: `pass`
- Decision: `randomized_holdout_candidate_promotion_packet_ready`
- Packet ready: `True`
- Candidate cases: `20`
- Random seed: `914`
- Pass rate: `1.0`
- Clean randomized cases: `20`
- Candidate packet authorized: `True`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_candidate_promotion_packet`

## Evidence Manifest

| Kind | Status | Ready | Promotion | Exists | Path | Role |
| --- | --- | --- | --- | --- | --- | --- |
| randomized_replay_review | pass | True | False | True | e\917\解释\randomized-target-hidden-holdout-replay-review\randomized_target_hidden_holdout_replay_review.json | authorizes candidate packet while blocking direct promotion |
| randomized_real_replay | pass | True | False | True | e\916\解释\randomized-target-hidden-holdout-real-replay\randomized_target_hidden_holdout_real_replay.json | proves the real checkpoint passes randomized target-hidden prompts |
| randomized_dry_run | pass | True | False | True | e\915\解释\randomized-target-hidden-holdout-dry-run\randomized_target_hidden_holdout_dry_run.json | proves the scoring contract rejects the fixed-only negative control |
| randomized_suite | pass | True | False | True | e\914\解释\randomized-target-hidden-holdout-suite\randomized_target_hidden_holdout_suite.json | defines the 20 target-hidden randomized prompts |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| replay_review_passed | pass | pass | replay review must pass |
| replay_review_ready | pass | True | review summary must be ready |
| candidate_packet_authorized | pass | True | review must authorize a candidate packet |
| review_blocks_direct_promotion | pass | {'approved_for_promotion': False, 'promotion_ready': False} | review must not widen the claim into promotion |
| review_routes_to_packet | pass | build_randomized_holdout_candidate_promotion_packet | review should route to this packet |
| real_replay_passed | pass | pass | real replay must pass |
| real_replay_ready | pass | True | real replay summary must be ready |
| real_model_signal_ready | pass | True | real replay must carry the randomized model-quality signal |
| dry_run_passed | pass | pass | dry-run must pass structurally |
| dry_run_ready | pass | True | dry-run summary must be ready |
| negative_control_rejected | pass | False | negative control must not pass |
| suite_passed | pass | pass | randomized suite must pass |
| suite_ready | pass | True | suite summary must be ready |
| candidate_count_at_least_twenty | pass | 20 | packet requires at least 20 randomized cases |
| suite_cases_match_summary | pass | {'cases': 20, 'summary': 20} | suite case list must match summary |
| case_counts_consistent | pass | [20, 20, 20, 20, 20] | suite, dry-run, replay, and review must cover the same case count |
| random_seed_consistent | pass | [914, 914, 914, 914] | all randomized reports must carry the same source seed |
| pass_rate_complete | pass | {'review': 1.0, 'real': 1.0} | candidate packet expects a 1.0 randomized replay pass rate |
| clean_randomized_cases_complete | pass | 20 | review must mark every randomized case clean |
| target_hidden_complete | pass | 20 | review must keep every randomized case target-hidden |
| no_task_hints_or_leakage | pass | {'hints': 0, 'leakage': 0} | review must report no hints or target leakage |
| all_evidence_files_exist | pass | [{'kind': 'randomized_replay_review', 'path': 'e\\917\\解释\\randomized-target-hidden-holdout-replay-review\\randomized_target_hidden_holdout_replay_review.json', 'exists': True, 'status': 'pass', 'decision': 'randomized_target_hidden_holdout_replay_review_clean_signal_candidate_packet_required', 'ready_key': 'randomized_target_hidden_holdout_replay_review_ready', 'ready_value': True, 'promotion_ready': False, 'role': 'authorizes candidate packet while blocking direct promotion'}, {'kind': 'randomized_real_replay', 'path': 'e\\916\\解释\\randomized-target-hidden-holdout-real-replay\\randomized_target_hidden_holdout_real_replay.json', 'exists': True, 'status': 'pass', 'decision': 'randomized_target_hidden_holdout_real_replay_passed_review_required', 'ready_key': 'randomized_target_hidden_holdout_real_replay_ready', 'ready_value': True, 'promotion_ready': False, 'role': 'proves the real checkpoint passes randomized target-hidden prompts'}, {'kind': 'randomized_dry_run', 'path': 'e\\915\\解释\\randomized-target-hidden-holdout-dry-run\\randomized_target_hidden_holdout_dry_run.json', 'exists': True, 'status': 'pass', 'decision': 'randomized_target_hidden_holdout_dry_run_passed', 'ready_key': 'randomized_target_hidden_holdout_dry_run_ready', 'ready_value': True, 'promotion_ready': False, 'role': 'proves the scoring contract rejects the fixed-only negative control'}, {'kind': 'randomized_suite', 'path': 'e\\914\\解释\\randomized-target-hidden-holdout-suite\\randomized_target_hidden_holdout_suite.json', 'exists': True, 'status': 'pass', 'decision': 'randomized_target_hidden_holdout_suite_ready', 'ready_key': 'randomized_target_hidden_holdout_suite_ready', 'ready_value': True, 'promotion_ready': False, 'role': 'defines the 20 target-hidden randomized prompts'}] | all packet source files must exist |
| all_inputs_keep_promotion_false | pass | [False, False, False, False] | candidate packet must not silently become promotion |

# MiniGPT randomized holdout publication registry entry

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_entry_ready`
- Entry ready: `True`
- Entry id: `randomized-holdout-publication-v928`
- Registry status: `registered`
- Bounded accepted: `True`
- Promotion: `False`
- Accepted claims: `1`
- Blocked claims: `3`
- Candidate cases: `20`
- Allowed use: `bounded_model_capability_governance_only`
- Claim: `bounded_randomized_target_hidden_holdout_claim_only`
- Boundary: `governance_lookup_only`
- Next step: `check_randomized_holdout_publication_registry_entry`

## Registry Entry

| Field | Value |
| --- | --- |
| entry_id | randomized-holdout-publication-v928 |
| registry_status | registered |
| entry_type | bounded_model_capability_publication |
| source_index_path | e\928\解释\randomized-holdout-publication-decision-index\randomized_holdout_publication_decision_index.json |
| source_index_decision | accept_bounded_randomized_holdout_publication |
| bounded_publication_accepted | True |
| promotion_ready | False |
| approved_for_promotion | False |
| accepted_claim_count | 1 |
| blocked_claim_count | 3 |
| candidate_case_count | 20 |
| random_seed | 914 |
| pass_rate | 1.0 |
| allowed_use | bounded_model_capability_governance_only |
| model_quality_claim | bounded_randomized_target_hidden_holdout_claim_only |
| decision_scope | bounded_randomized_holdout_publication_only |
| source_count | 3 |
| source_kinds | ['publication_decision', 'publication_review', 'publication_packet'] |
| consumer_boundary | governance_lookup_only |
| next_step | check_randomized_holdout_publication_registry_entry |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_index_file_exists | pass | e\928\解释\randomized-holdout-publication-decision-index\randomized_holdout_publication_decision_index.json | source publication decision index file must exist |
| source_index_passed | pass | pass | source publication decision index must pass |
| source_index_decision_ready | pass | randomized_holdout_publication_decision_index_ready | source publication decision index decision must be ready |
| source_index_summary_ready | pass | {'summary': True, 'index': True} | source index summary and body must be ready |
| indexed_decision_expected | pass | accept_bounded_randomized_holdout_publication | registry entry expects the bounded publication acceptance decision |
| bounded_publication_accepted | pass | {'summary': True, 'index': True} | registry entry only accepts bounded publication-ready indexes |
| accepted_claim_count | pass | 1 | registry entry expects exactly one accepted bounded claim |
| blocked_claim_count | pass | 3 | registry entry expects blocked claim boundaries |
| candidate_case_count | pass | 20 | registry entry expects the randomized 20-case floor |
| pass_rate_complete | pass | 1.0 | registry entry expects complete randomized replay pass rate |
| allowed_use_bounded | pass | {'summary': 'bounded_model_capability_governance_only', 'index': 'bounded_model_capability_governance_only'} | allowed use must stay bounded governance only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must stay bounded to randomized holdout |
| promotion_still_false | pass | {'summary': False, 'index': False} | registry entry must not enable direct promotion |
| approved_for_promotion_false | pass | {'summary': False, 'index': False} | direct promotion approval must remain false |
| source_count_expected | pass | {'summary': 3, 'rows': 3} | registry entry expects the three-source publication chain |
| source_kinds_expected | pass | ['publication_decision', 'publication_review', 'publication_packet'] | source kinds must keep publication decision, review, and packet order |
| source_checks_clean | pass | 0 | source index checks must be clean |
| source_next_step_matches | pass | build_randomized_holdout_publication_registry_entry | source index must route to registry entry build |

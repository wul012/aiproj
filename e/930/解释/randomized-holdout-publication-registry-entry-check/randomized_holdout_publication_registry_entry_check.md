# MiniGPT randomized holdout publication registry entry contract check

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_entry_contract_check_passed`
- Ready: `True`
- Source index: `e\928\解释\randomized-holdout-publication-decision-index\randomized_holdout_publication_decision_index.json`
- Original entry: `randomized-holdout-publication-v928`
- Rebuilt entry: `randomized-holdout-publication-v928`
- Original boundary: `governance_lookup_only`
- Rebuilt boundary: `governance_lookup_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_publication_decision_index_present | pass | e\928\解释\randomized-holdout-publication-decision-index\randomized_holdout_publication_decision_index.json | registry entry must record a source publication decision index |
| source_publication_decision_index_exists | pass | e\928\解释\randomized-holdout-publication-decision-index\randomized_holdout_publication_decision_index.json | source publication decision index must exist |
| status | pass | {'source': 'pass', 'rebuilt': 'pass'} | status must match the rebuilt registry entry |
| decision | pass | {'source': 'randomized_holdout_publication_registry_entry_ready', 'rebuilt': 'randomized_holdout_publication_registry_entry_ready'} | decision must match the rebuilt registry entry |
| failed_count | pass | {'source': 0, 'rebuilt': 0} | failed_count must match the rebuilt registry entry |
| summary.randomized_holdout_publication_registry_entry_ready | pass | {'source': True, 'rebuilt': True} | summary.randomized_holdout_publication_registry_entry_ready must match the rebuilt registry entry |
| summary.entry_id | pass | {'source': 'randomized-holdout-publication-v928', 'rebuilt': 'randomized-holdout-publication-v928'} | summary.entry_id must match the rebuilt registry entry |
| summary.registry_status | pass | {'source': 'registered', 'rebuilt': 'registered'} | summary.registry_status must match the rebuilt registry entry |
| summary.entry_type | pass | {'source': 'bounded_model_capability_publication', 'rebuilt': 'bounded_model_capability_publication'} | summary.entry_type must match the rebuilt registry entry |
| summary.bounded_publication_accepted | pass | {'source': True, 'rebuilt': True} | summary.bounded_publication_accepted must match the rebuilt registry entry |
| summary.promotion_ready | pass | {'source': False, 'rebuilt': False} | summary.promotion_ready must match the rebuilt registry entry |
| summary.approved_for_promotion | pass | {'source': False, 'rebuilt': False} | summary.approved_for_promotion must match the rebuilt registry entry |
| summary.accepted_claim_count | pass | {'source': 1, 'rebuilt': 1} | summary.accepted_claim_count must match the rebuilt registry entry |
| summary.blocked_claim_count | pass | {'source': 3, 'rebuilt': 3} | summary.blocked_claim_count must match the rebuilt registry entry |
| summary.candidate_case_count | pass | {'source': 20, 'rebuilt': 20} | summary.candidate_case_count must match the rebuilt registry entry |
| summary.random_seed | pass | {'source': 914, 'rebuilt': 914} | summary.random_seed must match the rebuilt registry entry |
| summary.pass_rate | pass | {'source': 1.0, 'rebuilt': 1.0} | summary.pass_rate must match the rebuilt registry entry |
| summary.allowed_use | pass | {'source': 'bounded_model_capability_governance_only', 'rebuilt': 'bounded_model_capability_governance_only'} | summary.allowed_use must match the rebuilt registry entry |
| summary.model_quality_claim | pass | {'source': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | summary.model_quality_claim must match the rebuilt registry entry |
| summary.decision_scope | pass | {'source': 'bounded_randomized_holdout_publication_only', 'rebuilt': 'bounded_randomized_holdout_publication_only'} | summary.decision_scope must match the rebuilt registry entry |
| summary.source_count | pass | {'source': 3, 'rebuilt': 3} | summary.source_count must match the rebuilt registry entry |
| summary.source_kinds | pass | {'source': ['publication_decision', 'publication_review', 'publication_packet'], 'rebuilt': ['publication_decision', 'publication_review', 'publication_packet']} | summary.source_kinds must match the rebuilt registry entry |
| summary.consumer_boundary | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.consumer_boundary must match the rebuilt registry entry |
| summary.next_step | pass | {'source': 'check_randomized_holdout_publication_registry_entry', 'rebuilt': 'check_randomized_holdout_publication_registry_entry'} | summary.next_step must match the rebuilt registry entry |
| registry_entry.entry_ready | pass | {'source': True, 'rebuilt': True} | registry_entry.entry_ready must match the rebuilt registry entry |
| registry_entry.entry_id | pass | {'source': 'randomized-holdout-publication-v928', 'rebuilt': 'randomized-holdout-publication-v928'} | registry_entry.entry_id must match the rebuilt registry entry |
| registry_entry.registry_status | pass | {'source': 'registered', 'rebuilt': 'registered'} | registry_entry.registry_status must match the rebuilt registry entry |
| registry_entry.entry_type | pass | {'source': 'bounded_model_capability_publication', 'rebuilt': 'bounded_model_capability_publication'} | registry_entry.entry_type must match the rebuilt registry entry |
| registry_entry.source_index_decision | pass | {'source': 'accept_bounded_randomized_holdout_publication', 'rebuilt': 'accept_bounded_randomized_holdout_publication'} | registry_entry.source_index_decision must match the rebuilt registry entry |
| registry_entry.bounded_publication_accepted | pass | {'source': True, 'rebuilt': True} | registry_entry.bounded_publication_accepted must match the rebuilt registry entry |
| registry_entry.promotion_ready | pass | {'source': False, 'rebuilt': False} | registry_entry.promotion_ready must match the rebuilt registry entry |
| registry_entry.approved_for_promotion | pass | {'source': False, 'rebuilt': False} | registry_entry.approved_for_promotion must match the rebuilt registry entry |
| registry_entry.accepted_claim_count | pass | {'source': 1, 'rebuilt': 1} | registry_entry.accepted_claim_count must match the rebuilt registry entry |
| registry_entry.blocked_claim_count | pass | {'source': 3, 'rebuilt': 3} | registry_entry.blocked_claim_count must match the rebuilt registry entry |
| registry_entry.candidate_case_count | pass | {'source': 20, 'rebuilt': 20} | registry_entry.candidate_case_count must match the rebuilt registry entry |
| registry_entry.random_seed | pass | {'source': 914, 'rebuilt': 914} | registry_entry.random_seed must match the rebuilt registry entry |
| registry_entry.pass_rate | pass | {'source': 1.0, 'rebuilt': 1.0} | registry_entry.pass_rate must match the rebuilt registry entry |
| registry_entry.allowed_use | pass | {'source': 'bounded_model_capability_governance_only', 'rebuilt': 'bounded_model_capability_governance_only'} | registry_entry.allowed_use must match the rebuilt registry entry |
| registry_entry.model_quality_claim | pass | {'source': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | registry_entry.model_quality_claim must match the rebuilt registry entry |
| registry_entry.decision_scope | pass | {'source': 'bounded_randomized_holdout_publication_only', 'rebuilt': 'bounded_randomized_holdout_publication_only'} | registry_entry.decision_scope must match the rebuilt registry entry |
| registry_entry.source_count | pass | {'source': 3, 'rebuilt': 3} | registry_entry.source_count must match the rebuilt registry entry |
| registry_entry.source_kinds | pass | {'source': ['publication_decision', 'publication_review', 'publication_packet'], 'rebuilt': ['publication_decision', 'publication_review', 'publication_packet']} | registry_entry.source_kinds must match the rebuilt registry entry |
| registry_entry.consumer_boundary | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | registry_entry.consumer_boundary must match the rebuilt registry entry |
| registry_entry.next_step | pass | {'source': 'check_randomized_holdout_publication_registry_entry', 'rebuilt': 'check_randomized_holdout_publication_registry_entry'} | registry_entry.next_step must match the rebuilt registry entry |

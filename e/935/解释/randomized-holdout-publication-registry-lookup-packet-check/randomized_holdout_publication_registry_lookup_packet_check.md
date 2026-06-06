# MiniGPT randomized holdout publication registry lookup packet contract check

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_lookup_packet_contract_check_passed`
- Ready: `True`
- Source review: `e\933\解释\randomized-holdout-publication-registry-manifest-review\randomized_holdout_publication_registry_manifest_review.json`
- Original lookup scope: `governance_lookup_only`
- Rebuilt lookup scope: `governance_lookup_only`
- Original rejected use: `production_promotion`
- Rebuilt rejected use: `production_promotion`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_manifest_review_present | pass | e\933\解释\randomized-holdout-publication-registry-manifest-review\randomized_holdout_publication_registry_manifest_review.json | lookup packet must record a source manifest review |
| source_manifest_review_exists | pass | e\933\解释\randomized-holdout-publication-registry-manifest-review\randomized_holdout_publication_registry_manifest_review.json | source manifest review must exist |
| status | pass | {'source': 'pass', 'rebuilt': 'pass'} | status must match the rebuilt lookup packet |
| decision | pass | {'source': 'randomized_holdout_publication_registry_lookup_packet_ready', 'rebuilt': 'randomized_holdout_publication_registry_lookup_packet_ready'} | decision must match the rebuilt lookup packet |
| failed_count | pass | {'source': 0, 'rebuilt': 0} | failed_count must match the rebuilt lookup packet |
| summary.randomized_holdout_publication_registry_lookup_packet_ready | pass | {'source': True, 'rebuilt': True} | summary.randomized_holdout_publication_registry_lookup_packet_ready must match the rebuilt lookup packet |
| summary.lookup_packet_id | pass | {'source': 'randomized-holdout-publication-registry-lookup-packet-v934', 'rebuilt': 'randomized-holdout-publication-registry-lookup-packet-v934'} | summary.lookup_packet_id must match the rebuilt lookup packet |
| summary.lookup_scope | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.lookup_scope must match the rebuilt lookup packet |
| summary.entry_count | pass | {'source': 1, 'rebuilt': 1} | summary.entry_count must match the rebuilt lookup packet |
| summary.lookup_ready | pass | {'source': True, 'rebuilt': True} | summary.lookup_ready must match the rebuilt lookup packet |
| summary.bounded_publication_accepted | pass | {'source': True, 'rebuilt': True} | summary.bounded_publication_accepted must match the rebuilt lookup packet |
| summary.promotion_ready | pass | {'source': False, 'rebuilt': False} | summary.promotion_ready must match the rebuilt lookup packet |
| summary.approved_for_promotion | pass | {'source': False, 'rebuilt': False} | summary.approved_for_promotion must match the rebuilt lookup packet |
| summary.consumer_boundary | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.consumer_boundary must match the rebuilt lookup packet |
| summary.allowed_use | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.allowed_use must match the rebuilt lookup packet |
| summary.rejected_use | pass | {'source': 'production_promotion', 'rebuilt': 'production_promotion'} | summary.rejected_use must match the rebuilt lookup packet |
| summary.next_step | pass | {'source': 'check_randomized_holdout_publication_registry_lookup_packet', 'rebuilt': 'check_randomized_holdout_publication_registry_lookup_packet'} | summary.next_step must match the rebuilt lookup packet |
| lookup_packet.packet_ready | pass | {'source': True, 'rebuilt': True} | lookup_packet.packet_ready must match the rebuilt lookup packet |
| lookup_packet.lookup_packet_id | pass | {'source': 'randomized-holdout-publication-registry-lookup-packet-v934', 'rebuilt': 'randomized-holdout-publication-registry-lookup-packet-v934'} | lookup_packet.lookup_packet_id must match the rebuilt lookup packet |
| lookup_packet.lookup_scope | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | lookup_packet.lookup_scope must match the rebuilt lookup packet |
| lookup_packet.registry_manifest_review_path | pass | {'source': 'e\\933\\解释\\randomized-holdout-publication-registry-manifest-review\\randomized_holdout_publication_registry_manifest_review.json', 'rebuilt': 'e\\933\\解释\\randomized-holdout-publication-registry-manifest-review\\randomized_holdout_publication_registry_manifest_review.json'} | lookup_packet.registry_manifest_review_path must match the rebuilt lookup packet |
| lookup_packet.entry_count | pass | {'source': 1, 'rebuilt': 1} | lookup_packet.entry_count must match the rebuilt lookup packet |
| lookup_packet.lookup_entries | pass | {'source': [{'lookup_key': 'publication:randomized-holdout-publication-v928', 'entry_id': 'randomized-holdout-publication-v928', 'registry_status': 'registered', 'bounded_publication_accepted': True, 'promotion_ready': False, 'consumer_boundary': 'governance_lookup_only', 'allowed_use': 'bounded_model_capability_governance_only', 'model_quality_claim': 'bounded_randomized_target_hidden_holdout_claim_only', 'random_seed': 914, 'pass_rate': 1.0}], 'rebuilt': [{'lookup_key': 'publication:randomized-holdout-publication-v928', 'entry_id': 'randomized-holdout-publication-v928', 'registry_status': 'registered', 'bounded_publication_accepted': True, 'promotion_ready': False, 'consumer_boundary': 'governance_lookup_only', 'allowed_use': 'bounded_model_capability_governance_only', 'model_quality_claim': 'bounded_randomized_target_hidden_holdout_claim_only', 'random_seed': 914, 'pass_rate': 1.0}]} | lookup_packet.lookup_entries must match the rebuilt lookup packet |
| lookup_packet.lookup_keys | pass | {'source': ['publication:randomized-holdout-publication-v928'], 'rebuilt': ['publication:randomized-holdout-publication-v928']} | lookup_packet.lookup_keys must match the rebuilt lookup packet |
| lookup_packet.lookup_ready | pass | {'source': True, 'rebuilt': True} | lookup_packet.lookup_ready must match the rebuilt lookup packet |
| lookup_packet.bounded_publication_accepted | pass | {'source': True, 'rebuilt': True} | lookup_packet.bounded_publication_accepted must match the rebuilt lookup packet |
| lookup_packet.promotion_ready | pass | {'source': False, 'rebuilt': False} | lookup_packet.promotion_ready must match the rebuilt lookup packet |
| lookup_packet.approved_for_promotion | pass | {'source': False, 'rebuilt': False} | lookup_packet.approved_for_promotion must match the rebuilt lookup packet |
| lookup_packet.consumer_boundary | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | lookup_packet.consumer_boundary must match the rebuilt lookup packet |
| lookup_packet.allowed_use | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | lookup_packet.allowed_use must match the rebuilt lookup packet |
| lookup_packet.rejected_use | pass | {'source': 'production_promotion', 'rebuilt': 'production_promotion'} | lookup_packet.rejected_use must match the rebuilt lookup packet |
| lookup_packet.next_step | pass | {'source': 'check_randomized_holdout_publication_registry_lookup_packet', 'rebuilt': 'check_randomized_holdout_publication_registry_lookup_packet'} | lookup_packet.next_step must match the rebuilt lookup packet |

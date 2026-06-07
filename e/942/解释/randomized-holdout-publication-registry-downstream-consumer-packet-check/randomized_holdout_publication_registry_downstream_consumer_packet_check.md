# MiniGPT randomized holdout publication registry downstream consumer packet contract check

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_packet_contract_check_passed`
- Ready: `True`
- Source review: `e\940\解释\randomized-holdout-publication-registry-downstream-receipt-review\randomized_holdout_publication_registry_downstream_receipt_review.json`
- Original granted use: `downstream_governance_lookup_only`
- Rebuilt granted use: `downstream_governance_lookup_only`
- Original promotion ready: `False`
- Rebuilt promotion ready: `False`
- Next step: `index_randomized_holdout_publication_registry_downstream_consumer_packet`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_receipt_review_present | pass | e\940\解释\randomized-holdout-publication-registry-downstream-receipt-review\randomized_holdout_publication_registry_downstream_receipt_review.json | consumer packet must record a source receipt review |
| source_receipt_review_exists | pass | e\940\解释\randomized-holdout-publication-registry-downstream-receipt-review\randomized_holdout_publication_registry_downstream_receipt_review.json | source receipt review must exist |
| status | pass | {'source': 'pass', 'rebuilt': 'pass'} | status must match the rebuilt consumer packet |
| decision | pass | {'source': 'randomized_holdout_publication_registry_downstream_consumer_packet_ready', 'rebuilt': 'randomized_holdout_publication_registry_downstream_consumer_packet_ready'} | decision must match the rebuilt consumer packet |
| failed_count | pass | {'source': 0, 'rebuilt': 0} | failed_count must match the rebuilt consumer packet |
| summary.randomized_holdout_publication_registry_downstream_consumer_packet_ready | pass | {'source': True, 'rebuilt': True} | summary.randomized_holdout_publication_registry_downstream_consumer_packet_ready must match the rebuilt consumer packet |
| summary.packet_id | pass | {'source': 'randomized-holdout-publication-registry-downstream-consumer-packet-v941', 'rebuilt': 'randomized-holdout-publication-registry-downstream-consumer-packet-v941'} | summary.packet_id must match the rebuilt consumer packet |
| summary.packet_status | pass | {'source': 'downstream_consumer_packet_ready', 'rebuilt': 'downstream_consumer_packet_ready'} | summary.packet_status must match the rebuilt consumer packet |
| summary.consumer_name | pass | {'source': 'publication_registry_governance_lookup_reader', 'rebuilt': 'publication_registry_governance_lookup_reader'} | summary.consumer_name must match the rebuilt consumer packet |
| summary.lookup_ready | pass | {'source': True, 'rebuilt': True} | summary.lookup_ready must match the rebuilt consumer packet |
| summary.granted_use | pass | {'source': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | summary.granted_use must match the rebuilt consumer packet |
| summary.blocked_uses | pass | {'source': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'rebuilt': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | summary.blocked_uses must match the rebuilt consumer packet |
| summary.entry_count | pass | {'source': 1, 'rebuilt': 1} | summary.entry_count must match the rebuilt consumer packet |
| summary.consumer_receipt_count | pass | {'source': 1, 'rebuilt': 1} | summary.consumer_receipt_count must match the rebuilt consumer packet |
| summary.lookup_key_count | pass | {'source': 1, 'rebuilt': 1} | summary.lookup_key_count must match the rebuilt consumer packet |
| summary.promotion_ready | pass | {'source': False, 'rebuilt': False} | summary.promotion_ready must match the rebuilt consumer packet |
| summary.approved_for_promotion | pass | {'source': False, 'rebuilt': False} | summary.approved_for_promotion must match the rebuilt consumer packet |
| summary.consumer_boundary | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.consumer_boundary must match the rebuilt consumer packet |
| summary.model_quality_claim | pass | {'source': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | summary.model_quality_claim must match the rebuilt consumer packet |
| summary.next_step | pass | {'source': 'check_randomized_holdout_publication_registry_downstream_consumer_packet', 'rebuilt': 'check_randomized_holdout_publication_registry_downstream_consumer_packet'} | summary.next_step must match the rebuilt consumer packet |
| packet.packet_ready | pass | {'source': True, 'rebuilt': True} | packet.packet_ready must match the rebuilt consumer packet |
| packet.packet_id | pass | {'source': 'randomized-holdout-publication-registry-downstream-consumer-packet-v941', 'rebuilt': 'randomized-holdout-publication-registry-downstream-consumer-packet-v941'} | packet.packet_id must match the rebuilt consumer packet |
| packet.packet_status | pass | {'source': 'downstream_consumer_packet_ready', 'rebuilt': 'downstream_consumer_packet_ready'} | packet.packet_status must match the rebuilt consumer packet |
| packet.receipt_review_path | pass | {'source': 'e\\940\\解释\\randomized-holdout-publication-registry-downstream-receipt-review\\randomized_holdout_publication_registry_downstream_receipt_review.json', 'rebuilt': 'e\\940\\解释\\randomized-holdout-publication-registry-downstream-receipt-review\\randomized_holdout_publication_registry_downstream_receipt_review.json'} | packet.receipt_review_path must match the rebuilt consumer packet |
| packet.consumer_name | pass | {'source': 'publication_registry_governance_lookup_reader', 'rebuilt': 'publication_registry_governance_lookup_reader'} | packet.consumer_name must match the rebuilt consumer packet |
| packet.consumer_boundary | pass | {'source': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | packet.consumer_boundary must match the rebuilt consumer packet |
| packet.granted_use | pass | {'source': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | packet.granted_use must match the rebuilt consumer packet |
| packet.blocked_uses | pass | {'source': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'rebuilt': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | packet.blocked_uses must match the rebuilt consumer packet |
| packet.entry_count | pass | {'source': 1, 'rebuilt': 1} | packet.entry_count must match the rebuilt consumer packet |
| packet.consumer_receipt_count | pass | {'source': 1, 'rebuilt': 1} | packet.consumer_receipt_count must match the rebuilt consumer packet |
| packet.lookup_keys | pass | {'source': ['publication:randomized-holdout-publication-v928'], 'rebuilt': ['publication:randomized-holdout-publication-v928']} | packet.lookup_keys must match the rebuilt consumer packet |
| packet.source_guard_sha256 | pass | {'source': '887540a6d58a8dc33517bc155b2fb25ff921f005123ff0d48efd7d46c3f0ce67', 'rebuilt': '887540a6d58a8dc33517bc155b2fb25ff921f005123ff0d48efd7d46c3f0ce67'} | packet.source_guard_sha256 must match the rebuilt consumer packet |
| packet.promotion_ready | pass | {'source': False, 'rebuilt': False} | packet.promotion_ready must match the rebuilt consumer packet |
| packet.approved_for_promotion | pass | {'source': False, 'rebuilt': False} | packet.approved_for_promotion must match the rebuilt consumer packet |
| packet.model_quality_claim | pass | {'source': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | packet.model_quality_claim must match the rebuilt consumer packet |
| packet.next_step | pass | {'source': 'check_randomized_holdout_publication_registry_downstream_consumer_packet', 'rebuilt': 'check_randomized_holdout_publication_registry_downstream_consumer_packet'} | packet.next_step must match the rebuilt consumer packet |
| packet_rows | pass | {'source': [{'packet_id': 'randomized-holdout-publication-registry-downstream-consumer-packet-v941', 'consumer_name': 'publication_registry_governance_lookup_reader', 'lookup_key': 'publication:randomized-holdout-publication-v928', 'entry_id': 'randomized-holdout-publication-v928', 'granted_use': 'downstream_governance_lookup_only', 'blocked_uses': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'promotion_ready': False, 'packet_status': 'downstream_consumer_packet_ready'}], 'rebuilt': [{'packet_id': 'randomized-holdout-publication-registry-downstream-consumer-packet-v941', 'consumer_name': 'publication_registry_governance_lookup_reader', 'lookup_key': 'publication:randomized-holdout-publication-v928', 'entry_id': 'randomized-holdout-publication-v928', 'granted_use': 'downstream_governance_lookup_only', 'blocked_uses': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'promotion_ready': False, 'packet_status': 'downstream_consumer_packet_ready'}]} | packet_rows must match the rebuilt consumer packet |

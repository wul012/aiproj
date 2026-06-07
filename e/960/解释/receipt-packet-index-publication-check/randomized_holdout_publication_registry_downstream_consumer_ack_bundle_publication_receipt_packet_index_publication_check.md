# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication contract check

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_contract_check_passed`
- Contract check ready: `True`
- Source review: `e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json`
- Original publication status: `published_for_downstream_receipt_packet_index_lookup_only`
- Rebuilt publication status: `published_for_downstream_receipt_packet_index_lookup_only`
- Original published use: `downstream_governance_lookup_only`
- Rebuilt published use: `downstream_governance_lookup_only`
- Original packet index rows: `1`
- Rebuilt packet index rows: `1`
- Original promotion ready: `False`
- Rebuilt promotion ready: `False`
- Next step: `index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_receipt_packet_index_review_exists | pass | e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json | source receipt packet index review must exist |
| status | pass | {'original': 'pass', 'rebuilt': 'pass'} | status must rebuild exactly |
| decision | pass | {'original': 'randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_ready', 'rebuilt': 'randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_ready'} | decision must rebuild exactly |
| failed_count | pass | {'original': 0, 'rebuilt': 0} | failed count must rebuild exactly |
| check_rows | pass | check_rows | publication check rows must rebuild exactly |
| summary.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_ready | pass | {'original': True, 'rebuilt': True} | summary.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_ready must rebuild exactly |
| summary.publication_id | pass | {'original': 'randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959', 'rebuilt': 'randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959'} | summary.publication_id must rebuild exactly |
| summary.publication_status | pass | {'original': 'published_for_downstream_receipt_packet_index_lookup_only', 'rebuilt': 'published_for_downstream_receipt_packet_index_lookup_only'} | summary.publication_status must rebuild exactly |
| summary.consumer_name | pass | {'original': 'publication_registry_governance_lookup_reader', 'rebuilt': 'publication_registry_governance_lookup_reader'} | summary.consumer_name must rebuild exactly |
| summary.published_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | summary.published_use must rebuild exactly |
| summary.publish_ready | pass | {'original': True, 'rebuilt': True} | summary.publish_ready must rebuild exactly |
| summary.lookup_ready | pass | {'original': True, 'rebuilt': True} | summary.lookup_ready must rebuild exactly |
| summary.contract_check_ready | pass | {'original': True, 'rebuilt': True} | summary.contract_check_ready must rebuild exactly |
| summary.packet_index_row_count | pass | {'original': 1, 'rebuilt': 1} | summary.packet_index_row_count must rebuild exactly |
| summary.source_packet_row_count | pass | {'original': 1, 'rebuilt': 1} | summary.source_packet_row_count must rebuild exactly |
| summary.source_evidence_count | pass | {'original': 2, 'rebuilt': 2} | summary.source_evidence_count must rebuild exactly |
| summary.promotion_ready | pass | {'original': False, 'rebuilt': False} | summary.promotion_ready must rebuild exactly |
| summary.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | summary.approved_for_promotion must rebuild exactly |
| summary.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.consumer_boundary must rebuild exactly |
| summary.model_quality_claim | pass | {'original': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | summary.model_quality_claim must rebuild exactly |
| publication.publication_ready | pass | {'original': True, 'rebuilt': True} | publication.publication_ready must rebuild exactly |
| publication.publication_id | pass | {'original': 'randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959', 'rebuilt': 'randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959'} | publication.publication_id must rebuild exactly |
| publication.publication_status | pass | {'original': 'published_for_downstream_receipt_packet_index_lookup_only', 'rebuilt': 'published_for_downstream_receipt_packet_index_lookup_only'} | publication.publication_status must rebuild exactly |
| publication.receipt_packet_index_review_path | pass | {'original': 'e\\958\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json', 'rebuilt': 'e\\958\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json'} | publication.receipt_packet_index_review_path must rebuild exactly |
| publication.receipt_packet_index_path | pass | {'original': 'e\\957\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.json', 'rebuilt': 'e\\957\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.json'} | publication.receipt_packet_index_path must rebuild exactly |
| publication.source_packet_path | pass | {'original': 'e\\955\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.json', 'rebuilt': 'e\\955\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.json'} | publication.source_packet_path must rebuild exactly |
| publication.source_packet_check_path | pass | {'original': 'e\\956\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check.json', 'rebuilt': 'e\\956\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check.json'} | publication.source_packet_check_path must rebuild exactly |
| publication.consumer_name | pass | {'original': 'publication_registry_governance_lookup_reader', 'rebuilt': 'publication_registry_governance_lookup_reader'} | publication.consumer_name must rebuild exactly |
| publication.published_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | publication.published_use must rebuild exactly |
| publication.publish_ready | pass | {'original': True, 'rebuilt': True} | publication.publish_ready must rebuild exactly |
| publication.lookup_ready | pass | {'original': True, 'rebuilt': True} | publication.lookup_ready must rebuild exactly |
| publication.contract_check_ready | pass | {'original': True, 'rebuilt': True} | publication.contract_check_ready must rebuild exactly |
| publication.packet_index_row_count | pass | {'original': 1, 'rebuilt': 1} | publication.packet_index_row_count must rebuild exactly |
| publication.source_packet_row_count | pass | {'original': 1, 'rebuilt': 1} | publication.source_packet_row_count must rebuild exactly |
| publication.source_evidence_count | pass | {'original': 2, 'rebuilt': 2} | publication.source_evidence_count must rebuild exactly |
| publication.promotion_ready | pass | {'original': False, 'rebuilt': False} | publication.promotion_ready must rebuild exactly |
| publication.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | publication.approved_for_promotion must rebuild exactly |
| publication.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | publication.consumer_boundary must rebuild exactly |
| publication.model_quality_claim | pass | {'original': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | publication.model_quality_claim must rebuild exactly |
| publication.next_step | pass | {'original': 'check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication', 'rebuilt': 'check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication'} | publication.next_step must rebuild exactly |

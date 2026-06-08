# MiniGPT randomized holdout publication receipt packet index publication receipt check v984

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_contract_check_v984_passed`
- Contract check ready: `True`
- Source review: `e\982\解释\publication-index-review-v982\randomized_holdout_publication_receipt_packet_index_publication_index_review_v982.json`
- Original receipt status: `publication_index_lookup_receipted`
- Rebuilt receipt status: `publication_index_lookup_receipted`
- Original granted use: `downstream_governance_lookup_only`
- Rebuilt granted use: `downstream_governance_lookup_only`
- Next step: `index_randomized_holdout_publication_receipt_packet_index_publication_receipt_v984`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_index_review_exists | pass | e\982\解释\publication-index-review-v982\randomized_holdout_publication_receipt_packet_index_publication_index_review_v982.json | source index review must exist |
| status | pass | {'original': 'pass', 'rebuilt': 'pass'} | status must rebuild exactly |
| decision | pass | {'original': 'randomized_holdout_publication_receipt_packet_index_publication_receipt_v983_ready', 'rebuilt': 'randomized_holdout_publication_receipt_packet_index_publication_receipt_v983_ready'} | decision must rebuild exactly |
| failed_count | pass | {'original': 0, 'rebuilt': 0} | failed count must rebuild exactly |
| consumer_receipts | pass | consumer_receipts | consumer receipts must rebuild exactly |
| summary.receipt_id | pass | {'original': 'randomized-holdout-publication-receipt-packet-index-publication-receipt-v983', 'rebuilt': 'randomized-holdout-publication-receipt-packet-index-publication-receipt-v983'} | summary.receipt_id must rebuild exactly |
| summary.receipt_type | pass | {'original': 'randomized_holdout_publication_receipt_packet_index_publication', 'rebuilt': 'randomized_holdout_publication_receipt_packet_index_publication'} | summary.receipt_type must rebuild exactly |
| summary.receipt_status | pass | {'original': 'publication_index_lookup_receipted', 'rebuilt': 'publication_index_lookup_receipted'} | summary.receipt_status must rebuild exactly |
| summary.consumer_name | pass | {'original': 'publication_registry_governance_lookup_reader', 'rebuilt': 'publication_registry_governance_lookup_reader'} | summary.consumer_name must rebuild exactly |
| summary.granted_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | summary.granted_use must rebuild exactly |
| summary.publication_index_row_count | pass | {'original': 1, 'rebuilt': 1} | summary.publication_index_row_count must rebuild exactly |
| summary.source_evidence_count | pass | {'original': 2, 'rebuilt': 2} | summary.source_evidence_count must rebuild exactly |
| summary.lookup_key_count | pass | {'original': 1, 'rebuilt': 1} | summary.lookup_key_count must rebuild exactly |
| summary.promotion_ready | pass | {'original': False, 'rebuilt': False} | summary.promotion_ready must rebuild exactly |
| summary.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | summary.approved_for_promotion must rebuild exactly |
| summary.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.consumer_boundary must rebuild exactly |
| summary.blocked_uses | pass | {'original': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'rebuilt': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | summary.blocked_uses must rebuild exactly |
| summary.next_step | pass | {'original': 'check_randomized_holdout_publication_receipt_packet_index_publication_receipt_v983', 'rebuilt': 'check_randomized_holdout_publication_receipt_packet_index_publication_receipt_v983'} | summary.next_step must rebuild exactly |
| receipt.receipt_ready | pass | {'original': True, 'rebuilt': True} | receipt.receipt_ready must rebuild exactly |
| receipt.receipt_id | pass | {'original': 'randomized-holdout-publication-receipt-packet-index-publication-receipt-v983', 'rebuilt': 'randomized-holdout-publication-receipt-packet-index-publication-receipt-v983'} | receipt.receipt_id must rebuild exactly |
| receipt.receipt_type | pass | {'original': 'randomized_holdout_publication_receipt_packet_index_publication', 'rebuilt': 'randomized_holdout_publication_receipt_packet_index_publication'} | receipt.receipt_type must rebuild exactly |
| receipt.receipt_status | pass | {'original': 'publication_index_lookup_receipted', 'rebuilt': 'publication_index_lookup_receipted'} | receipt.receipt_status must rebuild exactly |
| receipt.consumer_name | pass | {'original': 'publication_registry_governance_lookup_reader', 'rebuilt': 'publication_registry_governance_lookup_reader'} | receipt.consumer_name must rebuild exactly |
| receipt.requested_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | receipt.requested_use must rebuild exactly |
| receipt.granted_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | receipt.granted_use must rebuild exactly |
| receipt.index_review_path | pass | {'original': 'e\\982\\解释\\publication-index-review-v982\\randomized_holdout_publication_receipt_packet_index_publication_index_review_v982.json', 'rebuilt': 'e\\982\\解释\\publication-index-review-v982\\randomized_holdout_publication_receipt_packet_index_publication_index_review_v982.json'} | receipt.index_review_path must rebuild exactly |
| receipt.publication_index_row_count | pass | {'original': 1, 'rebuilt': 1} | receipt.publication_index_row_count must rebuild exactly |
| receipt.source_evidence_count | pass | {'original': 2, 'rebuilt': 2} | receipt.source_evidence_count must rebuild exactly |
| receipt.lookup_keys | pass | {'original': ['publication-index:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication-v979'], 'rebuilt': ['publication-index:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication-v979']} | receipt.lookup_keys must rebuild exactly |
| receipt.review_id | pass | {'original': 'randomized-holdout-publication-receipt-packet-index-publication-index-review-v982', 'rebuilt': 'randomized-holdout-publication-receipt-packet-index-publication-index-review-v982'} | receipt.review_id must rebuild exactly |
| receipt.review_status | pass | {'original': 'approved_for_publication_index_receipt_lookup_only', 'rebuilt': 'approved_for_publication_index_receipt_lookup_only'} | receipt.review_status must rebuild exactly |
| receipt.blocked_uses | pass | {'original': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'rebuilt': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | receipt.blocked_uses must rebuild exactly |
| receipt.promotion_ready | pass | {'original': False, 'rebuilt': False} | receipt.promotion_ready must rebuild exactly |
| receipt.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | receipt.approved_for_promotion must rebuild exactly |
| receipt.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | receipt.consumer_boundary must rebuild exactly |
| receipt.model_quality_claim | pass | {'original': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | receipt.model_quality_claim must rebuild exactly |
| receipt.source_publication_path | pass | {'original': 'e\\979\\解释\\publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication\\randomized_holdout_publication_receipt_packet_index_publication_v979.json', 'rebuilt': 'e\\979\\解释\\publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication\\randomized_holdout_publication_receipt_packet_index_publication_v979.json'} | receipt.source_publication_path must rebuild exactly |
| receipt.source_publication_check_path | pass | {'original': 'e\\980\\解释\\publication-receipt-packet-index-publication-check\\randomized_holdout_publication_receipt_packet_index_publication_check_v980.json', 'rebuilt': 'e\\980\\解释\\publication-receipt-packet-index-publication-check\\randomized_holdout_publication_receipt_packet_index_publication_check_v980.json'} | receipt.source_publication_check_path must rebuild exactly |
| receipt.next_step | pass | {'original': 'check_randomized_holdout_publication_receipt_packet_index_publication_receipt_v983', 'rebuilt': 'check_randomized_holdout_publication_receipt_packet_index_publication_receipt_v983'} | receipt.next_step must rebuild exactly |

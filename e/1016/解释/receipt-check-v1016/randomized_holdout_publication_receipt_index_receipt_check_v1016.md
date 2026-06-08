# MiniGPT randomized holdout publication receipt index receipt check v1016

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_contract_check_v1016_passed`
- Contract check ready: `True`
- Source review: `e\1014\解释\review-v1014\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json`
- Original receipt status: `publication_receipt_index_receipt_v1015_lookup_receipted`
- Rebuilt receipt status: `publication_receipt_index_receipt_v1015_lookup_receipted`
- Original granted use: `downstream_governance_lookup_only`
- Rebuilt granted use: `downstream_governance_lookup_only`
- Next step: `index_randomized_holdout_publication_receipt_index_receipt_v1016`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_receipt_index_review_exists | pass | e\1014\解释\review-v1014\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json | source receipt index review must exist |
| status | pass | {'original': 'pass', 'rebuilt': 'pass'} | status must rebuild exactly |
| decision | pass | {'original': 'randomized_holdout_publication_receipt_index_receipt_v1015_ready', 'rebuilt': 'randomized_holdout_publication_receipt_index_receipt_v1015_ready'} | decision must rebuild exactly |
| failed_count | pass | {'original': 0, 'rebuilt': 0} | failed count must rebuild exactly |
| receipt_index_review_sha256 | pass | {'original': 'e2f148cf5fe83377b23e3a5560f7a9df3219a3e21e625a4c62b63ca49ffd478d', 'rebuilt': 'e2f148cf5fe83377b23e3a5560f7a9df3219a3e21e625a4c62b63ca49ffd478d'} | source review digest must rebuild exactly |
| consumer_receipts | pass | consumer_receipts | consumer receipts must rebuild exactly |
| summary.randomized_holdout_publication_receipt_index_receipt_v1015_ready | pass | {'original': True, 'rebuilt': True} | summary.randomized_holdout_publication_receipt_index_receipt_v1015_ready must rebuild exactly |
| summary.receipt_id | pass | {'original': 'randomized-holdout-publication-receipt-index-receipt-v1015', 'rebuilt': 'randomized-holdout-publication-receipt-index-receipt-v1015'} | summary.receipt_id must rebuild exactly |
| summary.receipt_type | pass | {'original': 'randomized_holdout_publication_receipt_index_receipt', 'rebuilt': 'randomized_holdout_publication_receipt_index_receipt'} | summary.receipt_type must rebuild exactly |
| summary.receipt_status | pass | {'original': 'publication_receipt_index_receipt_v1015_lookup_receipted', 'rebuilt': 'publication_receipt_index_receipt_v1015_lookup_receipted'} | summary.receipt_status must rebuild exactly |
| summary.consumer_name | pass | {'original': 'publication_receipt_index_receipt_v1015_lookup_reader', 'rebuilt': 'publication_receipt_index_receipt_v1015_lookup_reader'} | summary.consumer_name must rebuild exactly |
| summary.granted_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | summary.granted_use must rebuild exactly |
| summary.receipt_index_row_count | pass | {'original': 1, 'rebuilt': 1} | summary.receipt_index_row_count must rebuild exactly |
| summary.source_evidence_count | pass | {'original': 2, 'rebuilt': 2} | summary.source_evidence_count must rebuild exactly |
| summary.lookup_key_count | pass | {'original': 1, 'rebuilt': 1} | summary.lookup_key_count must rebuild exactly |
| summary.promotion_ready | pass | {'original': False, 'rebuilt': False} | summary.promotion_ready must rebuild exactly |
| summary.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | summary.approved_for_promotion must rebuild exactly |
| summary.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.consumer_boundary must rebuild exactly |
| summary.blocked_uses | pass | {'original': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'rebuilt': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | summary.blocked_uses must rebuild exactly |
| summary.next_step | pass | {'original': 'check_randomized_holdout_publication_receipt_index_receipt_v1015', 'rebuilt': 'check_randomized_holdout_publication_receipt_index_receipt_v1015'} | summary.next_step must rebuild exactly |
| summary.passed_check_count | pass | {'original': 21, 'rebuilt': 21} | summary.passed_check_count must rebuild exactly |
| summary.failed_check_count | pass | {'original': 0, 'rebuilt': 0} | summary.failed_check_count must rebuild exactly |
| receipt.receipt_ready | pass | {'original': True, 'rebuilt': True} | receipt.receipt_ready must rebuild exactly |
| receipt.receipt_id | pass | {'original': 'randomized-holdout-publication-receipt-index-receipt-v1015', 'rebuilt': 'randomized-holdout-publication-receipt-index-receipt-v1015'} | receipt.receipt_id must rebuild exactly |
| receipt.receipt_type | pass | {'original': 'randomized_holdout_publication_receipt_index_receipt', 'rebuilt': 'randomized_holdout_publication_receipt_index_receipt'} | receipt.receipt_type must rebuild exactly |
| receipt.receipt_status | pass | {'original': 'publication_receipt_index_receipt_v1015_lookup_receipted', 'rebuilt': 'publication_receipt_index_receipt_v1015_lookup_receipted'} | receipt.receipt_status must rebuild exactly |
| receipt.consumer_name | pass | {'original': 'publication_receipt_index_receipt_v1015_lookup_reader', 'rebuilt': 'publication_receipt_index_receipt_v1015_lookup_reader'} | receipt.consumer_name must rebuild exactly |
| receipt.requested_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | receipt.requested_use must rebuild exactly |
| receipt.granted_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | receipt.granted_use must rebuild exactly |
| receipt.receipt_index_review_path | pass | {'original': 'e\\1014\\解释\\review-v1014\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json', 'rebuilt': 'e\\1014\\解释\\review-v1014\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json'} | receipt.receipt_index_review_path must rebuild exactly |
| receipt.receipt_index_row_count | pass | {'original': 1, 'rebuilt': 1} | receipt.receipt_index_row_count must rebuild exactly |
| receipt.source_evidence_count | pass | {'original': 2, 'rebuilt': 2} | receipt.source_evidence_count must rebuild exactly |
| receipt.lookup_keys | pass | {'original': ['publication-index-receipt-index-receipt-index-receipt-index-receipt:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1011'], 'rebuilt': ['publication-index-receipt-index-receipt-index-receipt-index-receipt:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1011']} | receipt.lookup_keys must rebuild exactly |
| receipt.review_id | pass | {'original': 'randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-review-v1014', 'rebuilt': 'randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-review-v1014'} | receipt.review_id must rebuild exactly |
| receipt.review_status | pass | {'original': 'approved_for_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_lookup_only', 'rebuilt': 'approved_for_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_lookup_only'} | receipt.review_status must rebuild exactly |
| receipt.blocked_uses | pass | {'original': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'], 'rebuilt': ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']} | receipt.blocked_uses must rebuild exactly |
| receipt.promotion_ready | pass | {'original': False, 'rebuilt': False} | receipt.promotion_ready must rebuild exactly |
| receipt.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | receipt.approved_for_promotion must rebuild exactly |
| receipt.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | receipt.consumer_boundary must rebuild exactly |
| receipt.model_quality_claim | pass | {'original': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | receipt.model_quality_claim must rebuild exactly |
| receipt.source_receipt_index_path | pass | {'original': 'e\\1013\\解释\\receipt-index-v1013\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.json', 'rebuilt': 'e\\1013\\解释\\receipt-index-v1013\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.json'} | receipt.source_receipt_index_path must rebuild exactly |
| receipt.source_receipt_path | pass | {'original': 'e\\1011\\解释\\receipt-v1011\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1011.json', 'rebuilt': 'e\\1011\\解释\\receipt-v1011\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1011.json'} | receipt.source_receipt_path must rebuild exactly |
| receipt.source_receipt_check_path | pass | {'original': 'e\\1012\\解释\\receipt-check-v1012\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1012.json', 'rebuilt': 'e\\1012\\解释\\receipt-check-v1012\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1012.json'} | receipt.source_receipt_check_path must rebuild exactly |
| receipt.next_step | pass | {'original': 'check_randomized_holdout_publication_receipt_index_receipt_v1015', 'rebuilt': 'check_randomized_holdout_publication_receipt_index_receipt_v1015'} | receipt.next_step must rebuild exactly |

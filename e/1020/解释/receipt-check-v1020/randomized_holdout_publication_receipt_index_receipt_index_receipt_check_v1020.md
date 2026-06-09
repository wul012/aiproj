# MiniGPT randomized holdout publication receipt index receipt index receipt check v1020

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_contract_check_v1020_passed`
- Contract check ready: `True`
- Source review: `e\1018\解释\receipt-index-review-v1018\randomized_holdout_publication_receipt_index_receipt_index_review_v1018.json`
- Original receipt status: `publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted`
- Rebuilt receipt status: `publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted`
- Original granted use: `downstream_governance_lookup_only`
- Rebuilt granted use: `downstream_governance_lookup_only`
- Next step: `index_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1020`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_receipt_index_review_exists | pass | e\1018\解释\receipt-index-review-v1018\randomized_holdout_publication_receipt_index_receipt_index_review_v1018.json | source receipt index review must exist |
| status | pass | {'original': 'pass', 'rebuilt': 'pass'} | status must rebuild exactly |
| decision | pass | {'original': 'randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019_ready', 'rebuilt': 'randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019_ready'} | decision must rebuild exactly |
| failed_count | pass | {'original': 0, 'rebuilt': 0} | failed count must rebuild exactly |
| receipt_index_review_sha256 | pass | {'original': '2f8bc7b2fe3b574802a8847a3a670eb179a61ba861e00a25a1d09e68f4449379', 'rebuilt': '2f8bc7b2fe3b574802a8847a3a670eb179a61ba861e00a25a1d09e68f4449379'} | source review digest must rebuild exactly |
| consumer_receipts | pass | consumer_receipts | consumer receipts must rebuild exactly |
| summary.randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019_ready | pass | {'original': True, 'rebuilt': True} | summary.randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019_ready must rebuild exactly |
| summary.receipt_id | pass | {'original': 'randomized-holdout-publication-receipt-index-receipt-index-receipt-v1019', 'rebuilt': 'randomized-holdout-publication-receipt-index-receipt-index-receipt-v1019'} | summary.receipt_id must rebuild exactly |
| summary.receipt_type | pass | {'original': 'randomized_holdout_publication_receipt_index_receipt_index_receipt', 'rebuilt': 'randomized_holdout_publication_receipt_index_receipt_index_receipt'} | summary.receipt_type must rebuild exactly |
| summary.receipt_status | pass | {'original': 'publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted', 'rebuilt': 'publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted'} | summary.receipt_status must rebuild exactly |
| summary.consumer_name | pass | {'original': 'publication_receipt_index_receipt_index_receipt_v1019_lookup_reader', 'rebuilt': 'publication_receipt_index_receipt_index_receipt_v1019_lookup_reader'} | summary.consumer_name must rebuild exactly |
| summary.granted_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | summary.granted_use must rebuild exactly |
| summary.receipt_index_row_count | pass | {'original': 1, 'rebuilt': 1} | summary.receipt_index_row_count must rebuild exactly |
| summary.source_evidence_count | pass | {'original': 2, 'rebuilt': 2} | summary.source_evidence_count must rebuild exactly |
| summary.lookup_key_count | pass | {'original': 1, 'rebuilt': 1} | summary.lookup_key_count must rebuild exactly |
| summary.promotion_ready | pass | {'original': False, 'rebuilt': False} | summary.promotion_ready must rebuild exactly |
| summary.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | summary.approved_for_promotion must rebuild exactly |
| summary.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.consumer_boundary must rebuild exactly |
| summary.model_quality_claim | pass | {'original': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | summary.model_quality_claim must rebuild exactly |
| summary.next_step | pass | {'original': 'check_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019', 'rebuilt': 'check_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019'} | summary.next_step must rebuild exactly |
| summary.passed_check_count | pass | {'original': 25, 'rebuilt': 25} | summary.passed_check_count must rebuild exactly |
| summary.failed_check_count | pass | {'original': 0, 'rebuilt': 0} | summary.failed_check_count must rebuild exactly |
| receipt.receipt_ready | pass | {'original': True, 'rebuilt': True} | receipt.receipt_ready must rebuild exactly |
| receipt.receipt_id | pass | {'original': 'randomized-holdout-publication-receipt-index-receipt-index-receipt-v1019', 'rebuilt': 'randomized-holdout-publication-receipt-index-receipt-index-receipt-v1019'} | receipt.receipt_id must rebuild exactly |
| receipt.receipt_type | pass | {'original': 'randomized_holdout_publication_receipt_index_receipt_index_receipt', 'rebuilt': 'randomized_holdout_publication_receipt_index_receipt_index_receipt'} | receipt.receipt_type must rebuild exactly |
| receipt.receipt_status | pass | {'original': 'publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted', 'rebuilt': 'publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted'} | receipt.receipt_status must rebuild exactly |
| receipt.consumer_name | pass | {'original': 'publication_receipt_index_receipt_index_receipt_v1019_lookup_reader', 'rebuilt': 'publication_receipt_index_receipt_index_receipt_v1019_lookup_reader'} | receipt.consumer_name must rebuild exactly |
| receipt.requested_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | receipt.requested_use must rebuild exactly |
| receipt.granted_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | receipt.granted_use must rebuild exactly |
| receipt.receipt_index_review_path | pass | {'original': 'e\\1018\\解释\\receipt-index-review-v1018\\randomized_holdout_publication_receipt_index_receipt_index_review_v1018.json', 'rebuilt': 'e\\1018\\解释\\receipt-index-review-v1018\\randomized_holdout_publication_receipt_index_receipt_index_review_v1018.json'} | receipt.receipt_index_review_path must rebuild exactly |
| receipt.receipt_index_review_sha256 | pass | {'original': '2f8bc7b2fe3b574802a8847a3a670eb179a61ba861e00a25a1d09e68f4449379', 'rebuilt': '2f8bc7b2fe3b574802a8847a3a670eb179a61ba861e00a25a1d09e68f4449379'} | receipt.receipt_index_review_sha256 must rebuild exactly |
| receipt.receipt_index_row_count | pass | {'original': 1, 'rebuilt': 1} | receipt.receipt_index_row_count must rebuild exactly |
| receipt.source_evidence_count | pass | {'original': 2, 'rebuilt': 2} | receipt.source_evidence_count must rebuild exactly |
| receipt.lookup_keys | pass | {'original': ['publication-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-v1015'], 'rebuilt': ['publication-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-v1015']} | receipt.lookup_keys must rebuild exactly |
| receipt.review_id | pass | {'original': 'randomized-holdout-publication-receipt-index-receipt-index-review-v1018', 'rebuilt': 'randomized-holdout-publication-receipt-index-receipt-index-review-v1018'} | receipt.review_id must rebuild exactly |
| receipt.review_status | pass | {'original': 'approved_for_publication_receipt_index_receipt_index_lookup_only', 'rebuilt': 'approved_for_publication_receipt_index_receipt_index_lookup_only'} | receipt.review_status must rebuild exactly |
| receipt.promotion_ready | pass | {'original': False, 'rebuilt': False} | receipt.promotion_ready must rebuild exactly |
| receipt.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | receipt.approved_for_promotion must rebuild exactly |
| receipt.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | receipt.consumer_boundary must rebuild exactly |
| receipt.model_quality_claim | pass | {'original': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | receipt.model_quality_claim must rebuild exactly |
| receipt.source_receipt_index_path | pass | {'original': 'e\\1017\\解释\\receipt-index-v1017\\randomized_holdout_publication_receipt_index_receipt_index_v1017.json', 'rebuilt': 'e\\1017\\解释\\receipt-index-v1017\\randomized_holdout_publication_receipt_index_receipt_index_v1017.json'} | receipt.source_receipt_index_path must rebuild exactly |
| receipt.source_receipt_path | pass | {'original': 'e\\1015\\解释\\receipt-v1015\\randomized_holdout_publication_receipt_index_receipt_v1015.json', 'rebuilt': 'e\\1015\\解释\\receipt-v1015\\randomized_holdout_publication_receipt_index_receipt_v1015.json'} | receipt.source_receipt_path must rebuild exactly |
| receipt.source_receipt_check_path | pass | {'original': 'e\\1016\\解释\\receipt-check-v1016\\randomized_holdout_publication_receipt_index_receipt_check_v1016.json', 'rebuilt': 'e\\1016\\解释\\receipt-check-v1016\\randomized_holdout_publication_receipt_index_receipt_check_v1016.json'} | receipt.source_receipt_check_path must rebuild exactly |
| receipt.source_review_path | pass | {'original': 'e\\1014\\解释\\review-v1014\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json', 'rebuilt': 'e\\1014\\解释\\review-v1014\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json'} | receipt.source_review_path must rebuild exactly |
| receipt.source_receipt_index_origin_path | pass | {'original': 'e\\1013\\解释\\receipt-index-v1013\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.json', 'rebuilt': 'e\\1013\\解释\\receipt-index-v1013\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.json'} | receipt.source_receipt_index_origin_path must rebuild exactly |
| receipt.next_step | pass | {'original': 'check_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019', 'rebuilt': 'check_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019'} | receipt.next_step must rebuild exactly |

# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication index receipt index receipt index receipt index review v1006

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006_ready`
- Review ready: `True`
- Review status: `approved_for_publication_index_receipt_index_receipt_index_receipt_index_receipt_lookup_only`
- Receipt index ready: `True`
- Lookup keys: `1`
- Source evidence: `2`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1006`

## Review

- Receipt index: `e\1005\解释\receipt-index-v1005\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005.json`
- Source receipt: `e\1003\解释\receipt-v1003\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.json`
- Source receipt check: `e\1004\解释\receipt-check-v1004\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_check_v1004.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | e\1005\解释\receipt-index-v1005\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['publication-index-receipt-index-receipt-index-receipt:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-index-receipt-v1003'] | lookup keys must use the publication-index-receipt-index-receipt-index-receipt namespace |
| index_rows_not_promoted | pass | [False] | receipt index review must not promote rows |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_digests | pass | ['75ff27b70cb90f8d2c188e28dbc24692eaf5e5b9618df143541b0a662897d429', 'f5cb481e64ee53e1831b3a67dca6f06be67bda4719f8800cf2409acedf9389d1'] | source evidence rows must carry SHA-256 digests |
| source_evidence_files_exist | pass | ['e\\1003\\解释\\receipt-v1003\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.json', 'e\\1004\\解释\\receipt-check-v1004\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_check_v1004.json'] | source evidence files must exist |
| source_receipt_file_exists | pass | {'index': 'e\\1003\\解释\\receipt-v1003\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.json', 'rows': ['e\\1003\\解释\\receipt-v1003\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.json']} | source receipt must still exist |
| source_receipt_check_file_exists | pass | {'index': 'e\\1004\\解释\\receipt-check-v1004\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_check_v1004.json', 'rows': ['e\\1004\\解释\\receipt-check-v1004\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_check_v1004.json']} | source receipt contract check must still exist |
| source_paths_match_rows | pass | {'receipt': 'e\\1003\\解释\\receipt-v1003\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.json', 'row_receipts': ['e\\1003\\解释\\receipt-v1003\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.json'], 'check': 'e\\1004\\解释\\receipt-check-v1004\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_check_v1004.json', 'row_checks': ['e\\1004\\解释\\receipt-check-v1004\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_check_v1004.json']} | receipt index body paths must match row paths |
| source_review_file_exists | pass | ['e\\1002\\解释\\review-v1002\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_review_v1002.json'] | source publication index review must still exist |
| source_receipt_index_file_exists | pass | ['e\\1001\\解释\\receipt-index-v1001\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001.json'] | source receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005 | source receipt index must route to review |

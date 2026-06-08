# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication index receipt index receipt index review v1002

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_review_v1002_ready`
- Review ready: `True`
- Review status: `approved_for_publication_index_receipt_index_receipt_index_receipt_lookup_only`
- Receipt index ready: `True`
- Lookup keys: `1`
- Source evidence: `2`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1002`

## Review

- Receipt index: `e\1001\解释\receipt-index-v1001\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001.json`
- Source receipt: `e\999\解释\publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json`
- Source receipt check: `e\1000\解释\receipt-index-receipt-check-v1000\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | e\1001\解释\receipt-index-v1001\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['publication-index-receipt-index-receipt:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999'] | lookup keys must use the publication-index-receipt-index-receipt namespace |
| index_rows_not_promoted | pass | [False] | receipt index review must not promote rows |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_digests | pass | ['f03a30064a9bbbc49d057d6d9435e5ed4295104a0ef34be0d7ee8d3a36043845', '272d0d7636da9e5d9c807cc51f71f160d786b9cdd3ead7f99ed0e73a1a1e0a30'] | source evidence rows must carry SHA-256 digests |
| source_evidence_files_exist | pass | ['e\\999\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json', 'e\\1000\\解释\\receipt-index-receipt-check-v1000\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.json'] | source evidence files must exist |
| source_receipt_file_exists | pass | {'index': 'e\\999\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json', 'rows': ['e\\999\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json']} | source receipt must still exist |
| source_receipt_check_file_exists | pass | {'index': 'e\\1000\\解释\\receipt-index-receipt-check-v1000\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.json', 'rows': ['e\\1000\\解释\\receipt-index-receipt-check-v1000\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.json']} | source receipt contract check must still exist |
| source_paths_match_rows | pass | {'receipt': 'e\\999\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json', 'row_receipts': ['e\\999\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json'], 'check': 'e\\1000\\解释\\receipt-index-receipt-check-v1000\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.json', 'row_checks': ['e\\1000\\解释\\receipt-index-receipt-check-v1000\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.json']} | receipt index body paths must match row paths |
| source_review_file_exists | pass | ['e\\998\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-index-review-v998\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998.json'] | source publication index review must still exist |
| source_receipt_index_file_exists | pass | ['e\\997\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-index-v997\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.json'] | source receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001 | source receipt index must route to review |

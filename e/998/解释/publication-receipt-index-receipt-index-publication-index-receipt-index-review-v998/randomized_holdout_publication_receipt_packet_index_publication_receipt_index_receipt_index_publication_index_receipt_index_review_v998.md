# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication index receipt index review v998

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_ready`
- Review ready: `True`
- Review status: `approved_for_publication_index_receipt_index_receipt_lookup_only`
- Receipt index ready: `True`
- Lookup keys: `1`
- Source evidence: `2`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v998`

## Review

- Receipt index: `e\997\解释\publication-receipt-index-receipt-index-publication-index-receipt-index-v997\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.json`
- Source receipt: `e\995\解释\publication-receipt-index-receipt-index-publication-index-receipt-v995\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.json`
- Source receipt check: `e\996\解释\publication-receipt-index-receipt-index-publication-index-receipt-check-v996\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | e\997\解释\publication-receipt-index-receipt-index-publication-index-receipt-index-v997\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['publication-index-receipt:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-v995'] | lookup keys must use the publication-index-receipt namespace |
| index_rows_not_promoted | pass | [False] | receipt index review must not promote rows |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_digests | pass | ['d7b91d8aa6f3f8f3f93b678ed407b68ce853b3a80df24aa58f32fe7c3cae296a', 'cc38f0ebb66aad754d875a15096c81610b208b257216d72dd9857a1ac0007497'] | source evidence rows must carry SHA-256 digests |
| source_evidence_files_exist | pass | ['e\\995\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-v995\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.json', 'e\\996\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-check-v996\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996.json'] | source evidence files must exist |
| source_receipt_file_exists | pass | {'index': 'e\\995\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-v995\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.json', 'rows': ['e\\995\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-v995\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.json']} | source receipt must still exist |
| source_receipt_check_file_exists | pass | {'index': 'e\\996\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-check-v996\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996.json', 'rows': ['e\\996\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-check-v996\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996.json']} | source receipt contract check must still exist |
| source_paths_match_rows | pass | {'receipt': 'e\\995\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-v995\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.json', 'row_receipts': ['e\\995\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-v995\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.json'], 'check': 'e\\996\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-check-v996\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996.json', 'row_checks': ['e\\996\\解释\\publication-receipt-index-receipt-index-publication-index-receipt-check-v996\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996.json']} | receipt index body paths must match row paths |
| source_review_file_exists | pass | ['e\\994\\解释\\publication-receipt-index-receipt-index-publication-index-review-v994\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994.json'] | source publication index review must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997 | source receipt index must route to review |

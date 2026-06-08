# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication index review v994

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_ready`
- Review ready: `True`
- Review status: `approved_for_publication_index_receipt_lookup_only`
- Publication ready: `True`
- Lookup keys: `1`
- Source evidence: `2`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v994`

## Review

- Publication index: `e\993\解释\publication-receipt-index-receipt-index-publication-index-v993\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993.json`
- Source publication: `e\991\解释\publication-receipt-index-receipt-index-publication-v991\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.json`
- Source publication check: `e\992\解释\publication-receipt-index-receipt-index-publication-check-v992\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| publication_index_file_exists | pass | e\993\解释\publication-receipt-index-receipt-index-publication-index-v993\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993.json | publication index file must exist |
| publication_index_passed | pass | pass | publication index must pass |
| publication_index_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_ready | publication index decision must be ready |
| publication_index_summary_ready | pass | {'summary': True, 'index': True} | publication index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| published_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | published use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | publication index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | publication index must include ready contract check |
| publication_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one publication index row |
| lookup_keys_present | pass | ['publication-index:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-v991'] | lookup keys must use the publication-index namespace |
| index_rows_not_promoted | pass | [False] | publication index review must not promote rows |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_digests | pass | ['da2bd9f46d0d09eaa0661b62fb97e4b65e143e0a81a6896e0a9f3b6dfbf0a46a', 'dd29cf19f56528d8b94dc1e283b598bfaab12ad046aceb6669b84a944ceea3a7'] | source evidence rows must carry SHA-256 digests |
| source_evidence_files_exist | pass | ['e\\991\\解释\\publication-receipt-index-receipt-index-publication-v991\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.json', 'e\\992\\解释\\publication-receipt-index-receipt-index-publication-check-v992\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992.json'] | source evidence files must exist |
| source_publication_file_exists | pass | e\991\解释\publication-receipt-index-receipt-index-publication-v991\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\992\解释\publication-receipt-index-receipt-index-publication-check-v992\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992.json | source publication check must still exist |
| source_review_file_exists | pass | ['e\\990\\解释\\publication-receipt-index-receipt-index-review-v990\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990.json'] | source review must still exist |
| source_receipt_index_file_exists | pass | ['e\\989\\解释\\publication-receipt-index-receipt-index-v989\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989.json'] | source receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | publication index review must not enable promotion |
| source_checks_clean | pass | 0 | source publication index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993 | source publication index must route to review |

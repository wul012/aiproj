# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication index v993

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_ready`
- Index ready: `True`
- Publication index: `randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-v993`
- Lookup scope: `downstream_governance_lookup_only`
- Lookup key count: `1`
- Published use: `downstream_governance_lookup_only`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993`

## Publication Index Rows

| Index | Lookup key | Publication | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-v993 | publication-index:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-v991 | randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-v991 | published_for_publication_receipt_index_receipt_index_lookup_only | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| publication | e\991\解释\publication-receipt-index-receipt-index-publication-v991\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.json | da2bd9f46d0d09eaa0661b62fb97e4b65e143e0a81a6896e0a9f3b6dfbf0a46a | pass |
| publication_check | e\992\解释\publication-receipt-index-receipt-index-publication-check-v992\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992.json | dd29cf19f56528d8b94dc1e283b598bfaab12ad046aceb6669b84a944ceea3a7 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| publication_file_exists | pass | e\991\解释\publication-receipt-index-receipt-index-publication-v991\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.json | publication file must exist |
| publication_check_file_exists | pass | e\992\解释\publication-receipt-index-receipt-index-publication-check-v992\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992.json | publication contract check file must exist |
| publication_passed | pass | pass | publication must pass |
| publication_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_ready | publication decision must be ready |
| publication_summary_ready | pass | {'summary': True, 'publication': True} | publication summary and body must be ready |
| publication_status_ready | pass | {'summary': 'published_for_publication_receipt_index_receipt_index_lookup_only', 'publication': 'published_for_publication_receipt_index_receipt_index_lookup_only'} | publication must be lookup-only published |
| publication_check_passed | pass | pass | publication contract check must pass |
| publication_check_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_contract_check_v992_passed | publication contract check decision must pass |
| contract_check_ready | pass | True | publication contract check must be ready |
| publication_status_matches_check | pass | {'publication': 'published_for_publication_receipt_index_receipt_index_lookup_only', 'original': 'published_for_publication_receipt_index_receipt_index_lookup_only', 'rebuilt': 'published_for_publication_receipt_index_receipt_index_lookup_only'} | publication status must match contract check |
| published_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'publication': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | published use must stay downstream lookup only |
| lookup_key_count | pass | {'summary': 1, 'original': 1, 'rebuilt': 1, 'publication': 1} | publication index requires one lookup key |
| source_evidence_count | pass | {'summary': 2, 'original': 2, 'rebuilt': 2} | publication index requires two source evidence rows |
| source_review_file_exists | pass | e\990\解释\publication-receipt-index-receipt-index-review-v990\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990.json | source review must still exist |
| source_receipt_index_file_exists | pass | e\989\解释\publication-receipt-index-receipt-index-v989\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989.json | source receipt index must still exist |
| source_receipt_file_exists | pass | e\987\解释\publication-receipt-index-receipt-v987\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\988\解释\publication-receipt-index-receipt-check-v988\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.json | source receipt check must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'publication': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'publication': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'approved': False, 'publication': False, 'original': False, 'rebuilt': False} | publication index must not enable promotion |
| source_publication_checks_clean | pass | 0 | source publication checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'publication': 'check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991', 'check': 'index_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v992'} | source next steps must route to check then index |

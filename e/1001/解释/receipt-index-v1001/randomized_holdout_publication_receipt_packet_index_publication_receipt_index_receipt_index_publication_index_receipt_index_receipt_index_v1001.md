# MiniGPT randomized holdout publication receipt packet index publication receipt index receipt index publication index receipt index receipt index v1001

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_ready`
- Index ready: `True`
- Receipt index: `randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-index-v1001`
- Lookup scope: `downstream_governance_lookup_only`
- Lookup key count: `1`
- Granted use: `downstream_governance_lookup_only`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001`

## Receipt Index Rows

| Index | Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-index-v1001 | publication-index-receipt-index-receipt:randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999 | randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999 | publication_index_receipt_index_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | e\999\解释\publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | f03a30064a9bbbc49d057d6d9435e5ed4295104a0ef34be0d7ee8d3a36043845 | pass |
| receipt_check | e\1000\解释\receipt-index-receipt-check-v1000\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.json | 272d0d7636da9e5d9c807cc51f71f160d786b9cdd3ead7f99ed0e73a1a1e0a30 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_file_exists | pass | e\999\解释\publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | receipt file must exist |
| receipt_check_file_exists | pass | e\1000\解释\receipt-index-receipt-check-v1000\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.json | receipt contract check file must exist |
| receipt_passed | pass | pass | receipt must pass |
| receipt_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999_ready | receipt decision must be ready |
| receipt_summary_ready | pass | {'summary': True, 'receipt': True} | receipt summary and body must be ready |
| receipt_status_ready | pass | {'summary': 'publication_index_receipt_index_lookup_receipted', 'receipt': 'publication_index_receipt_index_lookup_receipted'} | receipt must be receipt-index lookup receipted |
| receipt_check_passed | pass | pass | receipt contract check must pass |
| receipt_check_decision_ready | pass | randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_contract_check_v1000_passed | receipt contract check decision must pass |
| contract_check_ready | pass | True | receipt contract check must be ready |
| receipt_status_matches_check | pass | {'receipt': 'publication_index_receipt_index_lookup_receipted', 'original': 'publication_index_receipt_index_lookup_receipted', 'rebuilt': 'publication_index_receipt_index_lookup_receipted'} | receipt status must match contract check |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'receipt': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_key_count | pass | {'summary': 1, 'original': 1, 'rebuilt': 1, 'receipt': 1} | receipt index requires one lookup key |
| receipt_index_row_count | pass | {'summary': 1, 'receipt': 1} | receipt index receipt requires one indexed row |
| source_evidence_count | pass | {'summary': 2, 'receipt': 2} | receipt index receipt requires two source evidence rows |
| source_receipt_index_review_file_exists | pass | e\998\解释\publication-receipt-index-receipt-index-publication-index-receipt-index-review-v998\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998.json | source receipt index review must still exist |
| source_receipt_index_file_exists | pass | e\997\解释\publication-receipt-index-receipt-index-publication-index-receipt-index-v997\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.json | source receipt index must still exist |
| source_receipt_file_exists | pass | e\995\解释\publication-receipt-index-receipt-index-publication-index-receipt-v995\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v995.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\996\解释\publication-receipt-index-receipt-index-publication-index-receipt-check-v996\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996.json | source receipt contract check must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'receipt': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'approved': False, 'receipt': False, 'original': False, 'rebuilt': False} | receipt index must not enable promotion |
| source_receipt_checks_clean | pass | 0 | source receipt checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'receipt': 'check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999', 'check': 'index_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v1000'} | source next steps must route to check then index |

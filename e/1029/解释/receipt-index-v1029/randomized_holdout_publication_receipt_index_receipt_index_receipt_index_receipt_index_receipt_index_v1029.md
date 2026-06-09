# MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index v1029

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029_ready`
- Index ready: `True`
- Receipt index: `randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-v1029`
- Lookup scope: `downstream_governance_lookup_only`
- Lookup key count: `1`
- Granted use: `downstream_governance_lookup_only`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029`

## Receipt Index Rows

| Index | Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-v1029 | publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1027 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1027 | publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | e\1027\解释\receipt-v1027\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json | 663eff0afa5c2dfbf86eaf34522d7872f27978496bfafcfe84c31d71b6750e3b | pass |
| receipt_check | e\1028\解释\receipt-check-v1028\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json | e6b025f3f5ad99336110eabb26846ea13a5449e6f8ebb8c38ff8c4a9390da394 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_file_exists | pass | e\1027\解释\receipt-v1027\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json | receipt file must exist |
| receipt_check_file_exists | pass | e\1028\解释\receipt-check-v1028\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json | receipt contract check file must exist |
| receipt_passed | pass | pass | receipt must pass |
| receipt_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_ready | receipt decision must be ready |
| receipt_summary_ready | pass | {'summary': True, 'receipt': True} | receipt summary and body must be ready |
| receipt_status_ready | pass | {'summary': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted', 'receipt': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted'} | receipt must be lookup receipted |
| receipt_check_passed | pass | pass | receipt contract check must pass |
| receipt_check_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1028_passed | receipt contract check decision must pass |
| contract_check_ready | pass | True | receipt contract check must be ready |
| receipt_status_matches_check | pass | {'receipt': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted', 'original': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted', 'rebuilt': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted'} | receipt status must match contract check |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'receipt': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_key_count | pass | {'summary': 1, 'original': 1, 'rebuilt': 1, 'receipt': 1} | receipt index requires one lookup key |
| source_evidence_count | pass | {'summary': 2, 'receipt': 2} | receipt index receipt requires two source evidence rows |
| source_receipt_index_review_file_exists | pass | e\1026\解释\receipt-index-review-v1026\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json | source receipt index review must still exist |
| source_receipt_index_file_exists | pass | e\1025\解释\receipt-index-v1025\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.json | source receipt index must still exist |
| source_receipt_file_exists | pass | e\1023\解释\receipt-v1023\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\1024\解释\receipt-check-v1024\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_check_v1024.json | source receipt contract check must still exist |
| source_review_file_exists | pass | e\1022\解释\receipt-index-review-v1022\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022.json | source review must still exist |
| source_origin_index_file_exists | pass | e\1021\解释\receipt-index-v1021\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021.json | source origin receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'receipt': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'receipt': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'approved': False, 'receipt': False, 'original': False, 'rebuilt': False} | receipt index must not enable promotion |
| source_receipt_checks_clean | pass | 0 | source receipt checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'receipt': 'check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027', 'check': 'index_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1028'} | source next steps must route to check then index |

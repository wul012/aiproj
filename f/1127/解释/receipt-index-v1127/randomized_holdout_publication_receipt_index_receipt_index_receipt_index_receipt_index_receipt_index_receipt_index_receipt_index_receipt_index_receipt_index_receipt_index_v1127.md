# MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index v1127

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1127_ready`
- Index ready: `True`
- Receipt index: `randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-v1127`
- Lookup scope: `downstream_governance_lookup_only`
- Lookup key count: `1`
- Granted use: `downstream_governance_lookup_only`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1127`

## Receipt Index Rows

| Index | Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-v1127 | publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1125 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1125 | publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | f\1125\解释\receipt-v1125\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125.json | e0bbafa57796e9b4f8cb51ca38629190afb5ba19c77d259d85eff157cb39f827 | pass |
| receipt_check | f\1126\解释\receipt-check-v1126\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126.json | 5f824750925a194b022f896601dc3559e4b9468d28fc3239382b4c6c96bb9487 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_file_exists | pass | f\1125\解释\receipt-v1125\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125.json | receipt file must exist |
| receipt_check_file_exists | pass | f\1126\解释\receipt-check-v1126\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1126.json | receipt contract check file must exist |
| receipt_passed | pass | pass | receipt must pass |
| receipt_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_ready | receipt decision must be ready |
| receipt_summary_ready | pass | {'summary': True, 'receipt': True} | receipt summary and body must be ready |
| receipt_status_ready | pass | {'summary': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted', 'receipt': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted'} | receipt must be lookup receipted |
| receipt_check_passed | pass | pass | receipt contract check must pass |
| receipt_check_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1126_passed | receipt contract check decision must pass |
| contract_check_ready | pass | True | receipt contract check must be ready |
| receipt_status_matches_check | pass | {'receipt': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted', 'original': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted', 'rebuilt': 'publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted'} | receipt status must match contract check |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'receipt': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_key_count | pass | {'summary': 1, 'original': 1, 'rebuilt': 1, 'receipt': 1} | receipt index requires one lookup key |
| source_evidence_count | pass | {'summary': 2, 'receipt': 2} | receipt index receipt requires two source evidence rows |
| source_receipt_index_review_file_exists | pass | f\1124\解释\receipt-index-review-v1124\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1124.json | source receipt index review must still exist |
| source_receipt_index_file_exists | pass | f\1123\解释\receipt-index-v1123\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1123.json | source receipt index must still exist |
| source_receipt_file_exists | pass | f\1121\解释\receipt-v1121\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1121.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | f\1122\解释\receipt-check-v1122\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1122.json | source receipt contract check must still exist |
| source_review_file_exists | pass | f\1120\解释\receipt-index-review-v1120\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1120.json | source review must still exist |
| source_origin_index_file_exists | pass | f\1119\解释\receipt-index-v1119\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1119.json | source origin receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'receipt': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'receipt': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'approved': False, 'receipt': False, 'original': False, 'rebuilt': False} | receipt index must not enable promotion |
| source_receipt_checks_clean | pass | 0 | source receipt checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'receipt': 'check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125', 'check': 'index_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1126'} | source next steps must route to check then index |

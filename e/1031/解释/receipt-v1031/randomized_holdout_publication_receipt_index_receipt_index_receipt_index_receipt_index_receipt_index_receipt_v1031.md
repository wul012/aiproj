# MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt v1031

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_ready`
- Receipt ready: `True`
- Receipt status: `publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_lookup_receipted`
- Consumer: `publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Lookup keys: `1`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031`

## Receipt Boundary

- Source review: `e\1030\解释\receipt-index-review-v1030\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1030.json`
- Source receipt index: `e\1029\解释\receipt-index-v1029\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029.json`
- Source receipt: `e\1027\解释\receipt-v1027\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json`
- Source receipt check: `e\1028\解释\receipt-check-v1028\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json`
- Source origin review: `e\1026\解释\receipt-index-review-v1026\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json`
- Source origin receipt index: `e\1025\解释\receipt-index-v1025\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.json`

## Consumer Receipts

| Consumer | Lookup key | Receipt index | Source receipt | Receipt | Granted use | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_lookup_reader | publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1027 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-v1029 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1027 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1031 | downstream_governance_lookup_only | False | publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_review_file_exists | pass | e\1030\解释\receipt-index-review-v1030\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1030.json | receipt index review file must exist |
| receipt_index_review_passed | pass | pass | receipt index review must pass |
| receipt_index_review_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1030_ready | receipt index review decision must be ready |
| receipt_index_review_summary_ready | pass | {'summary': True, 'review': True} | receipt index review summary and body must be ready |
| review_status_allowed | pass | {'summary': 'approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only', 'review': 'approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only'} | review must approve lookup-only receipt recording |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| lookup_only_granted_use | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| receipt_index_lookup_ready | pass | {'receipt_index': True, 'summary_lookup': True, 'review_lookup': True} | receipt index lookup must be ready |
| contract_check_ready | pass | {'summary': True, 'review': True} | source contract check must be ready |
| index_rows_present | pass | {'rows': 1, 'summary': 1} | receipt must cover one receipt index row |
| source_evidence_count | pass | {'rows': 2, 'summary': 2} | receipt must preserve two source evidence rows |
| source_evidence_digests_present | pass | ['663eff0afa5c2dfbf86eaf34522d7872f27978496bfafcfe84c31d71b6750e3b', 'e6b025f3f5ad99336110eabb26846ea13a5449e6f8ebb8c38ff8c4a9390da394'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| lookup_keys_source_namespace | pass | ['publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1027'] | lookup keys must use the v1029 source namespace |
| index_rows_not_promoted | pass | [False] | receipt index rows must not be promoted |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | receipt must not enable promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_receipt_index_file_exists | pass | e\1029\解释\receipt-index-v1029\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029.json | source receipt index must still exist |
| source_receipt_file_exists | pass | e\1027\解释\receipt-v1027\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\1028\解释\receipt-check-v1028\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json | source receipt contract check must still exist |
| source_review_file_exists | pass | e\1026\解释\receipt-index-review-v1026\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json | source review must still exist |
| source_receipt_index_origin_file_exists | pass | e\1025\解释\receipt-index-v1025\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.json | source receipt index origin must still exist |
| source_checks_clean | pass | 0 | source receipt index review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1030 | source receipt index review must route to receipt |

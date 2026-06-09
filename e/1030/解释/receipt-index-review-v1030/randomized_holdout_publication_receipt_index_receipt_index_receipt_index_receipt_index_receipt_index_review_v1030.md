# MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index review v1030

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1030_ready`
- Review ready: `True`
- Review status: `approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only`
- Receipt index rows: `1`
- Lookup keys: `1`
- Source evidence: `2`
- Lookup ready: `True`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1030`

## Review Summary

- Receipt index path: `e\1029\解释\receipt-index-v1029\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029.json`
- Source receipt: `e\1027\解释\receipt-v1027\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json`
- Source receipt check: `e\1028\解释\receipt-check-v1028\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json`
- Source review: `e\1026\解释\receipt-index-review-v1026\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json`
- Source receipt index: `e\1025\解释\receipt-index-v1025\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.json`

## Receipt Index Rows

| Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- |
| publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1027 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1027 | publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | e\1027\解释\receipt-v1027\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json | 663eff0afa5c2dfbf86eaf34522d7872f27978496bfafcfe84c31d71b6750e3b | pass |
| receipt_check | e\1028\解释\receipt-check-v1028\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json | e6b025f3f5ad99336110eabb26846ea13a5449e6f8ebb8c38ff8c4a9390da394 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | e\1029\解释\receipt-index-v1029\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1027'] | lookup keys must use the v1029 receipt-index namespace |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_digests_present | pass | ['663eff0afa5c2dfbf86eaf34522d7872f27978496bfafcfe84c31d71b6750e3b', 'e6b025f3f5ad99336110eabb26846ea13a5449e6f8ebb8c38ff8c4a9390da394'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_receipt_file_exists | pass | {'index': 'e\\1027\\解释\\receipt-v1027\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json', 'rows': ['e\\1027\\解释\\receipt-v1027\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json']} | source receipt must still exist |
| source_receipt_check_file_exists | pass | {'index': 'e\\1028\\解释\\receipt-check-v1028\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json', 'rows': ['e\\1028\\解释\\receipt-check-v1028\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json']} | source receipt contract check must still exist |
| source_review_file_exists | pass | ['e\\1026\\解释\\receipt-index-review-v1026\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json'] | source review must still exist |
| source_receipt_index_file_exists | pass | ['e\\1025\\解释\\receipt-index-v1025\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.json'] | source receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029 | source receipt index must route to review |

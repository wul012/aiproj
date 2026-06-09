# MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index review v1050

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1050_ready`
- Review ready: `True`
- Review status: `approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only`
- Receipt index rows: `1`
- Lookup keys: `1`
- Source evidence: `2`
- Lookup ready: `True`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1050`

## Review Summary

- Receipt index path: `e\1049\解释\receipt-index-v1049\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1049.json`
- Source receipt: `e\1047\解释\receipt-v1047\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1047.json`
- Source receipt check: `e\1048\解释\receipt-check-v1048\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1048.json`
- Source review: `e\1046\解释\receipt-index-review-v1046\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1046.json`
- Source receipt index: `e\1045\解释\receipt-index-v1045\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1045.json`

## Receipt Index Rows

| Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- |
| publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1047 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1047 | publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1047_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | e\1047\解释\receipt-v1047\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1047.json | 50d2d30ab47f12272d3afb523e558f7446e55769968db4dab23c57cb980fc58a | pass |
| receipt_check | e\1048\解释\receipt-check-v1048\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1048.json | c1246dfcf54ea43fcee6606eeb27805bf90e2bb640f5e2ffa85267e8dad27725 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | e\1049\解释\receipt-index-v1049\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1049.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1049_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1047'] | lookup keys must use the v1049 receipt-index namespace |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_digests_present | pass | ['50d2d30ab47f12272d3afb523e558f7446e55769968db4dab23c57cb980fc58a', 'c1246dfcf54ea43fcee6606eeb27805bf90e2bb640f5e2ffa85267e8dad27725'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_receipt_file_exists | pass | {'index': 'e\\1047\\解释\\receipt-v1047\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1047.json', 'rows': ['e\\1047\\解释\\receipt-v1047\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1047.json']} | source receipt must still exist |
| source_receipt_check_file_exists | pass | {'index': 'e\\1048\\解释\\receipt-check-v1048\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1048.json', 'rows': ['e\\1048\\解释\\receipt-check-v1048\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1048.json']} | source receipt contract check must still exist |
| source_review_file_exists | pass | ['e\\1046\\解释\\receipt-index-review-v1046\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1046.json'] | source review must still exist |
| source_receipt_index_file_exists | pass | ['e\\1045\\解释\\receipt-index-v1045\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1045.json'] | source receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1049 | source receipt index must route to review |

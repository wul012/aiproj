# MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index review v1094

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1094_ready`
- Review ready: `True`
- Review status: `approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only`
- Receipt index rows: `1`
- Lookup keys: `1`
- Source evidence: `2`
- Lookup ready: `True`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1094`

## Review Summary

- Receipt index path: `e\1093\解释\receipt-index-v1093\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1093.json`
- Source receipt: `e\1091\解释\receipt-v1091\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1091.json`
- Source receipt check: `e\1092\解释\receipt-check-v1092\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1092.json`
- Source review: `e\1090\解释\receipt-index-review-v1090\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1090.json`
- Source receipt index: `e\1089\解释\receipt-index-v1089\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1089.json`

## Receipt Index Rows

| Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- |
| publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1091 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1091 | publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1091_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | e\1091\解释\receipt-v1091\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1091.json | 784b4ff00325f9ef684c182a879a5e6f7fe789231d961e08b0a3e61432be2d23 | pass |
| receipt_check | e\1092\解释\receipt-check-v1092\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1092.json | 23b00cafacc4145ad2b3a163b2ad0663b00e04d0862f3ad78f12df9022862b4f | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | e\1093\解释\receipt-index-v1093\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1093.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1093_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1091'] | lookup keys must use the v1093 receipt-index namespace |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_digests_present | pass | ['784b4ff00325f9ef684c182a879a5e6f7fe789231d961e08b0a3e61432be2d23', '23b00cafacc4145ad2b3a163b2ad0663b00e04d0862f3ad78f12df9022862b4f'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_receipt_file_exists | pass | {'index': 'e\\1091\\解释\\receipt-v1091\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1091.json', 'rows': ['e\\1091\\解释\\receipt-v1091\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1091.json']} | source receipt must still exist |
| source_receipt_check_file_exists | pass | {'index': 'e\\1092\\解释\\receipt-check-v1092\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1092.json', 'rows': ['e\\1092\\解释\\receipt-check-v1092\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1092.json']} | source receipt contract check must still exist |
| source_review_file_exists | pass | ['e\\1090\\解释\\receipt-index-review-v1090\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1090.json'] | source review must still exist |
| source_receipt_index_file_exists | pass | ['e\\1089\\解释\\receipt-index-v1089\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1089.json'] | source receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1093 | source receipt index must route to review |

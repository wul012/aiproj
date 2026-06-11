# MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index review v1108

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1108_ready`
- Review ready: `True`
- Review status: `approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only`
- Receipt index rows: `1`
- Lookup keys: `1`
- Source evidence: `2`
- Lookup ready: `True`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1108`

## Review Summary

- Receipt index path: `f\1107\解释\receipt-index-v1107\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107.json`
- Source receipt: `f\1105\解释\receipt-v1105\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1105.json`
- Source receipt check: `f\1106\解释\receipt-check-v1106\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1106.json`
- Source review: `f\1104\解释\receipt-index-review-v1104\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1104.json`
- Source receipt index: `f\1103\解释\receipt-index-v1103\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1103.json`

## Receipt Index Rows

| Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- |
| publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1105 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1105 | publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1105_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | f\1105\解释\receipt-v1105\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1105.json | e295e9a8bbbea67120e01392f09416d4e866c96a811349d57c3742306256de4f | pass |
| receipt_check | f\1106\解释\receipt-check-v1106\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1106.json | d31bd48213ab26b1f138aeccc3831e99de3eba44f7661e8b5ff949f7257964b5 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | f\1107\解释\receipt-index-v1107\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1105'] | lookup keys must use the v1107 receipt-index namespace |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_digests_present | pass | ['e295e9a8bbbea67120e01392f09416d4e866c96a811349d57c3742306256de4f', 'd31bd48213ab26b1f138aeccc3831e99de3eba44f7661e8b5ff949f7257964b5'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_receipt_file_exists | pass | {'index': 'f\\1105\\解释\\receipt-v1105\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1105.json', 'rows': ['f\\1105\\解释\\receipt-v1105\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1105.json']} | source receipt must still exist |
| source_receipt_check_file_exists | pass | {'index': 'f\\1106\\解释\\receipt-check-v1106\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1106.json', 'rows': ['f\\1106\\解释\\receipt-check-v1106\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1106.json']} | source receipt contract check must still exist |
| source_review_file_exists | pass | ['f\\1104\\解释\\receipt-index-review-v1104\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1104.json'] | source review must still exist |
| source_receipt_index_file_exists | pass | ['f\\1103\\解释\\receipt-index-v1103\\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1103.json'] | source receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107 | source receipt index must route to review |

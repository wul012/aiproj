# MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt v1125

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_ready`
- Receipt ready: `True`
- Receipt status: `publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted`
- Consumer: `publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Lookup keys: `1`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125`

## Receipt Boundary

- Source review: `f\1124\解释\receipt-index-review-v1124\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1124.json`
- Source receipt index: `f\1123\解释\receipt-index-v1123\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1123.json`
- Source receipt: `f\1121\解释\receipt-v1121\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1121.json`
- Source receipt check: `f\1122\解释\receipt-check-v1122\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1122.json`
- Source origin review: `f\1120\解释\receipt-index-review-v1120\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1120.json`
- Source origin receipt index: `f\1119\解释\receipt-index-v1119\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1119.json`

## Consumer Receipts

| Consumer | Lookup key | Receipt index | Source receipt | Receipt | Granted use | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_reader | publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1121 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-v1123 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1121 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1125 | downstream_governance_lookup_only | False | publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1125_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_review_file_exists | pass | f\1124\解释\receipt-index-review-v1124\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1124.json | receipt index review file must exist |
| receipt_index_review_passed | pass | pass | receipt index review must pass |
| receipt_index_review_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1124_ready | receipt index review decision must be ready |
| receipt_index_review_summary_ready | pass | {'summary': True, 'review': True} | receipt index review summary and body must be ready |
| review_status_allowed | pass | {'summary': 'approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only', 'review': 'approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only'} | review must approve lookup-only receipt recording |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| lookup_only_granted_use | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| receipt_index_lookup_ready | pass | {'receipt_index': True, 'summary_lookup': True, 'review_lookup': True} | receipt index lookup must be ready |
| contract_check_ready | pass | {'summary': True, 'review': True} | source contract check must be ready |
| index_rows_present | pass | {'rows': 1, 'summary': 1} | receipt must cover one receipt index row |
| source_evidence_count | pass | {'rows': 2, 'summary': 2} | receipt must preserve two source evidence rows |
| source_evidence_digests_present | pass | ['2c3708e62b8b171e65092e47e910a05a779d43b0deaeb753e487aecc33bfa0e8', 'f4edb82a0353b7ff9008c657c014fa9bad028b9692841b126f2788050d92058f'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| lookup_keys_source_namespace | pass | ['publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1121'] | lookup keys must use the source receipt-index namespace |
| index_rows_not_promoted | pass | [False] | receipt index rows must not be promoted |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | receipt must not enable promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_receipt_index_file_exists | pass | f\1123\解释\receipt-index-v1123\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1123.json | source receipt index must still exist |
| source_receipt_file_exists | pass | f\1121\解释\receipt-v1121\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1121.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | f\1122\解释\receipt-check-v1122\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1122.json | source receipt contract check must still exist |
| source_review_file_exists | pass | f\1120\解释\receipt-index-review-v1120\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1120.json | source review must still exist |
| source_receipt_index_origin_file_exists | pass | f\1119\解释\receipt-index-v1119\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1119.json | source receipt index origin must still exist |
| source_checks_clean | pass | 0 | source receipt index review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1124 | source receipt index review must route to receipt |

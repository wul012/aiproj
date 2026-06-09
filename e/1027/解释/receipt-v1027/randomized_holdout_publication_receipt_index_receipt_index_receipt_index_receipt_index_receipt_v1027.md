# MiniGPT randomized holdout publication receipt index receipt index receipt index receipt index receipt v1027

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_ready`
- Receipt ready: `True`
- Receipt status: `publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted`
- Consumer: `publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Lookup keys: `1`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027`

## Receipt Boundary

- Source review: `e\1026\解释\receipt-index-review-v1026\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json`
- Source receipt index: `e\1025\解释\receipt-index-v1025\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.json`
- Source receipt: `e\1023\解释\receipt-v1023\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023.json`
- Source receipt check: `e\1024\解释\receipt-check-v1024\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_check_v1024.json`
- Source origin review: `e\1022\解释\receipt-index-review-v1022\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022.json`
- Source origin receipt index: `e\1021\解释\receipt-index-v1021\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021.json`

## Consumer Receipts

| Consumer | Lookup key | Receipt index | Source receipt | Receipt | Granted use | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_reader | publication-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-v1023 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-v1025 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-v1023 | randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-v1027 | downstream_governance_lookup_only | False | publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_review_file_exists | pass | e\1026\解释\receipt-index-review-v1026\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json | receipt index review file must exist |
| receipt_index_review_passed | pass | pass | receipt index review must pass |
| receipt_index_review_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026_ready | receipt index review decision must be ready |
| receipt_index_review_summary_ready | pass | {'summary': True, 'review': True} | receipt index review summary and body must be ready |
| review_status_allowed | pass | {'summary': 'approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only', 'review': 'approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only'} | review must approve lookup-only receipt recording |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| lookup_only_granted_use | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| receipt_index_lookup_ready | pass | {'receipt_index': True, 'summary_lookup': True, 'review_lookup': True} | receipt index lookup must be ready |
| contract_check_ready | pass | {'summary': True, 'review': True} | source contract check must be ready |
| index_rows_present | pass | {'rows': 1, 'summary': 1} | receipt must cover one receipt index row |
| source_evidence_count | pass | {'rows': 2, 'summary': 2} | receipt must preserve two source evidence rows |
| source_evidence_digests_present | pass | ['1fb41139143fafac96413a218e18965e0ab13cfacea8db3b11a5984660a4fe07', 'ebea813ed587aaa2786697938e079f50e7eba7ab2a2bf562d49c37bf0178b1de'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| lookup_keys_source_namespace | pass | ['publication-receipt-index-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-v1023'] | lookup keys must use the v1025 source namespace |
| index_rows_not_promoted | pass | [False] | receipt index rows must not be promoted |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | receipt must not enable promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_receipt_index_file_exists | pass | e\1025\解释\receipt-index-v1025\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.json | source receipt index must still exist |
| source_receipt_file_exists | pass | e\1023\解释\receipt-v1023\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\1024\解释\receipt-check-v1024\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_check_v1024.json | source receipt contract check must still exist |
| source_review_file_exists | pass | e\1022\解释\receipt-index-review-v1022\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022.json | source review must still exist |
| source_receipt_index_origin_file_exists | pass | e\1021\解释\receipt-index-v1021\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021.json | source receipt index origin must still exist |
| source_checks_clean | pass | 0 | source receipt index review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1026 | source receipt index review must route to receipt |

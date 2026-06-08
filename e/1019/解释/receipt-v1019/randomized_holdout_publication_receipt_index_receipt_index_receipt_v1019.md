# MiniGPT randomized holdout publication receipt index receipt index receipt v1019

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019_ready`
- Receipt ready: `True`
- Receipt status: `publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted`
- Consumer: `publication_receipt_index_receipt_index_receipt_v1019_lookup_reader`
- Granted use: `downstream_governance_lookup_only`
- Lookup keys: `1`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019`

## Receipt Boundary

- Source review: `e\1018\解释\receipt-index-review-v1018\randomized_holdout_publication_receipt_index_receipt_index_review_v1018.json`
- Source receipt index: `e\1017\解释\receipt-index-v1017\randomized_holdout_publication_receipt_index_receipt_index_v1017.json`
- Source receipt: `e\1015\解释\receipt-v1015\randomized_holdout_publication_receipt_index_receipt_v1015.json`
- Source receipt check: `e\1016\解释\receipt-check-v1016\randomized_holdout_publication_receipt_index_receipt_check_v1016.json`
- Source origin review: `e\1014\解释\review-v1014\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json`
- Source origin receipt index: `e\1013\解释\receipt-index-v1013\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.json`

## Consumer Receipts

| Consumer | Lookup key | Receipt index | Source receipt | Receipt | Granted use | Promotion | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| publication_receipt_index_receipt_index_receipt_v1019_lookup_reader | publication-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-v1015 | randomized-holdout-publication-receipt-index-receipt-index-v1017 | randomized-holdout-publication-receipt-index-receipt-v1015 | randomized-holdout-publication-receipt-index-receipt-index-receipt-v1019 | downstream_governance_lookup_only | False | publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_review_file_exists | pass | e\1018\解释\receipt-index-review-v1018\randomized_holdout_publication_receipt_index_receipt_index_review_v1018.json | receipt index review file must exist |
| receipt_index_review_passed | pass | pass | receipt index review must pass |
| receipt_index_review_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_review_v1018_ready | receipt index review decision must be ready |
| receipt_index_review_summary_ready | pass | {'summary': True, 'review': True} | receipt index review summary and body must be ready |
| review_status_allowed | pass | {'summary': 'approved_for_publication_receipt_index_receipt_index_lookup_only', 'review': 'approved_for_publication_receipt_index_receipt_index_lookup_only'} | review must approve lookup-only receipt recording |
| requested_use_allowed | pass | downstream_governance_lookup_only | requested use must stay downstream governance lookup only |
| lookup_only_granted_use | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| receipt_index_lookup_ready | pass | {'receipt_index': True, 'summary_lookup': True, 'review_lookup': True} | receipt index lookup must be ready |
| contract_check_ready | pass | {'summary': True, 'review': True} | source contract check must be ready |
| index_rows_present | pass | {'rows': 1, 'summary': 1} | receipt must cover one receipt index row |
| source_evidence_count | pass | {'rows': 2, 'summary': 2} | receipt must preserve two source evidence rows |
| source_evidence_digests_present | pass | ['2a81e9821dd2c3ad834bb099e96afa3c74599c7a362426c7788fc03b4fea2b41', '4de8f78c43b5625af2a7927ebab108a2bbc91d638f5ba4fc4e1e9f76b533d96d'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| lookup_keys_source_namespace | pass | ['publication-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-v1015'] | lookup keys must use the v1017 source namespace |
| index_rows_not_promoted | pass | [False] | receipt index rows must not be promoted |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | receipt must not enable promotion |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| source_receipt_index_file_exists | pass | e\1017\解释\receipt-index-v1017\randomized_holdout_publication_receipt_index_receipt_index_v1017.json | source receipt index must still exist |
| source_receipt_file_exists | pass | e\1015\解释\receipt-v1015\randomized_holdout_publication_receipt_index_receipt_v1015.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\1016\解释\receipt-check-v1016\randomized_holdout_publication_receipt_index_receipt_check_v1016.json | source receipt contract check must still exist |
| source_review_file_exists | pass | e\1014\解释\review-v1014\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json | source review must still exist |
| source_receipt_index_origin_file_exists | pass | e\1013\解释\receipt-index-v1013\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.json | source receipt index origin must still exist |
| source_checks_clean | pass | 0 | source receipt index review checks must be clean |
| source_next_step_matches | pass | record_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1018 | source receipt index review must route to receipt |

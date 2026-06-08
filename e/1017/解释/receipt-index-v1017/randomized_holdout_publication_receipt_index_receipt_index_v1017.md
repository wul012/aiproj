# MiniGPT randomized holdout publication receipt index receipt index v1017

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_v1017_ready`
- Index ready: `True`
- Receipt index: `randomized-holdout-publication-receipt-index-receipt-index-v1017`
- Lookup scope: `downstream_governance_lookup_only`
- Lookup key count: `1`
- Granted use: `downstream_governance_lookup_only`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_receipt_index_receipt_index_v1017`

## Receipt Index Rows

| Index | Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-receipt-index-receipt-index-v1017 | publication-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-v1015 | randomized-holdout-publication-receipt-index-receipt-v1015 | publication_receipt_index_receipt_v1015_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | e\1015\解释\receipt-v1015\randomized_holdout_publication_receipt_index_receipt_v1015.json | 2a81e9821dd2c3ad834bb099e96afa3c74599c7a362426c7788fc03b4fea2b41 | pass |
| receipt_check | e\1016\解释\receipt-check-v1016\randomized_holdout_publication_receipt_index_receipt_check_v1016.json | 4de8f78c43b5625af2a7927ebab108a2bbc91d638f5ba4fc4e1e9f76b533d96d | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_file_exists | pass | e\1015\解释\receipt-v1015\randomized_holdout_publication_receipt_index_receipt_v1015.json | receipt file must exist |
| receipt_check_file_exists | pass | e\1016\解释\receipt-check-v1016\randomized_holdout_publication_receipt_index_receipt_check_v1016.json | receipt contract check file must exist |
| receipt_passed | pass | pass | receipt must pass |
| receipt_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_v1015_ready | receipt decision must be ready |
| receipt_summary_ready | pass | {'summary': True, 'receipt': True} | receipt summary and body must be ready |
| receipt_status_ready | pass | {'summary': 'publication_receipt_index_receipt_v1015_lookup_receipted', 'receipt': 'publication_receipt_index_receipt_v1015_lookup_receipted'} | receipt must be lookup receipted |
| receipt_check_passed | pass | pass | receipt contract check must pass |
| receipt_check_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_contract_check_v1016_passed | receipt contract check decision must pass |
| contract_check_ready | pass | True | receipt contract check must be ready |
| receipt_status_matches_check | pass | {'receipt': 'publication_receipt_index_receipt_v1015_lookup_receipted', 'original': 'publication_receipt_index_receipt_v1015_lookup_receipted', 'rebuilt': 'publication_receipt_index_receipt_v1015_lookup_receipted'} | receipt status must match contract check |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'receipt': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_key_count | pass | {'summary': 1, 'original': 1, 'rebuilt': 1, 'receipt': 1} | receipt index requires one lookup key |
| source_evidence_count | pass | {'summary': 2, 'receipt': 2} | receipt index receipt requires two source evidence rows |
| source_receipt_index_review_file_exists | pass | e\1014\解释\review-v1014\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json | source receipt index review must still exist |
| source_receipt_index_file_exists | pass | e\1013\解释\receipt-index-v1013\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.json | source receipt index must still exist |
| source_receipt_file_exists | pass | e\1011\解释\receipt-v1011\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1011.json | source receipt must still exist |
| source_receipt_check_file_exists | pass | e\1012\解释\receipt-check-v1012\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1012.json | source receipt contract check must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'receipt': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'approved': False, 'receipt': False, 'original': False, 'rebuilt': False} | receipt index must not enable promotion |
| source_receipt_checks_clean | pass | 0 | source receipt checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'receipt': 'check_randomized_holdout_publication_receipt_index_receipt_v1015', 'check': 'index_randomized_holdout_publication_receipt_index_receipt_v1016'} | source next steps must route to check then index |

# MiniGPT randomized holdout publication receipt index receipt index review v1018

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_review_v1018_ready`
- Review ready: `True`
- Review status: `approved_for_publication_receipt_index_receipt_index_lookup_only`
- Receipt index rows: `1`
- Lookup keys: `1`
- Source evidence: `2`
- Lookup ready: `True`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1018`

## Review Summary

- Receipt index path: `e\1017\解释\receipt-index-v1017\randomized_holdout_publication_receipt_index_receipt_index_v1017.json`
- Source receipt: `e\1015\解释\receipt-v1015\randomized_holdout_publication_receipt_index_receipt_v1015.json`
- Source receipt check: `e\1016\解释\receipt-check-v1016\randomized_holdout_publication_receipt_index_receipt_check_v1016.json`
- Source review: `e\1014\解释\review-v1014\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json`
- Source receipt index: `e\1013\解释\receipt-index-v1013\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.json`

## Receipt Index Rows

| Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- |
| publication-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-v1015 | randomized-holdout-publication-receipt-index-receipt-v1015 | publication_receipt_index_receipt_v1015_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | e\1015\解释\receipt-v1015\randomized_holdout_publication_receipt_index_receipt_v1015.json | 2a81e9821dd2c3ad834bb099e96afa3c74599c7a362426c7788fc03b4fea2b41 | pass |
| receipt_check | e\1016\解释\receipt-check-v1016\randomized_holdout_publication_receipt_index_receipt_check_v1016.json | 4de8f78c43b5625af2a7927ebab108a2bbc91d638f5ba4fc4e1e9f76b533d96d | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | e\1017\解释\receipt-index-v1017\randomized_holdout_publication_receipt_index_receipt_index_v1017.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_v1017_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['publication-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-v1015'] | lookup keys must use the v1017 short receipt-index namespace |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_digests_present | pass | ['2a81e9821dd2c3ad834bb099e96afa3c74599c7a362426c7788fc03b4fea2b41', '4de8f78c43b5625af2a7927ebab108a2bbc91d638f5ba4fc4e1e9f76b533d96d'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_receipt_file_exists | pass | {'index': 'e\\1015\\解释\\receipt-v1015\\randomized_holdout_publication_receipt_index_receipt_v1015.json', 'rows': ['e\\1015\\解释\\receipt-v1015\\randomized_holdout_publication_receipt_index_receipt_v1015.json']} | source receipt must still exist |
| source_receipt_check_file_exists | pass | {'index': 'e\\1016\\解释\\receipt-check-v1016\\randomized_holdout_publication_receipt_index_receipt_check_v1016.json', 'rows': ['e\\1016\\解释\\receipt-check-v1016\\randomized_holdout_publication_receipt_index_receipt_check_v1016.json']} | source receipt contract check must still exist |
| source_review_file_exists | pass | ['e\\1014\\解释\\review-v1014\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1014.json'] | source review must still exist |
| source_receipt_index_file_exists | pass | ['e\\1013\\解释\\receipt-index-v1013\\randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1013.json'] | source receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_index_receipt_index_v1017 | source receipt index must route to review |

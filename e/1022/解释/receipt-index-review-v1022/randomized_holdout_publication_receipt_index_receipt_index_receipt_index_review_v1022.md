# MiniGPT randomized holdout publication receipt index receipt index receipt index review v1022

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022_ready`
- Review ready: `True`
- Review status: `approved_for_publication_receipt_index_receipt_index_receipt_index_lookup_only`
- Receipt index rows: `1`
- Lookup keys: `1`
- Source evidence: `2`
- Lookup ready: `True`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1022`

## Review Summary

- Receipt index path: `e\1021\解释\receipt-index-v1021\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021.json`
- Source receipt: `e\1019\解释\receipt-v1019\randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019.json`
- Source receipt check: `e\1020\解释\receipt-check-v1020\randomized_holdout_publication_receipt_index_receipt_index_receipt_check_v1020.json`
- Source review: `e\1018\解释\receipt-index-review-v1018\randomized_holdout_publication_receipt_index_receipt_index_review_v1018.json`
- Source receipt index: `e\1017\解释\receipt-index-v1017\randomized_holdout_publication_receipt_index_receipt_index_v1017.json`

## Receipt Index Rows

| Lookup key | Receipt | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- |
| publication-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-v1019 | randomized-holdout-publication-receipt-index-receipt-index-receipt-v1019 | publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt | e\1019\解释\receipt-v1019\randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019.json | 72a11a9e54776e70f54659b1a06f0027910ca75bb631b9fb9af405e686eb54fc | pass |
| receipt_check | e\1020\解释\receipt-check-v1020\randomized_holdout_publication_receipt_index_receipt_index_receipt_check_v1020.json | 40af5d979e7ad930212b9cc76619c88c585f9f6f02aa9a1e59f7fdf0c55fabe1 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_index_file_exists | pass | e\1021\解释\receipt-index-v1021\randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021.json | receipt index file must exist |
| receipt_index_passed | pass | pass | receipt index must pass |
| receipt_index_decision_ready | pass | randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021_ready | receipt index decision must be ready |
| receipt_index_summary_ready | pass | {'summary': True, 'index': True} | receipt index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt index must include a ready contract check |
| receipt_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt index row |
| lookup_keys_present | pass | ['publication-receipt-index-receipt-index-receipt-index:randomized-holdout-publication-receipt-index-receipt-index-receipt-v1019'] | lookup keys must use the v1021 receipt-index namespace |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_digests_present | pass | ['72a11a9e54776e70f54659b1a06f0027910ca75bb631b9fb9af405e686eb54fc', '40af5d979e7ad930212b9cc76619c88c585f9f6f02aa9a1e59f7fdf0c55fabe1'] | source evidence digests must be present |
| source_evidence_status_pass | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_receipt_file_exists | pass | {'index': 'e\\1019\\解释\\receipt-v1019\\randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019.json', 'rows': ['e\\1019\\解释\\receipt-v1019\\randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019.json']} | source receipt must still exist |
| source_receipt_check_file_exists | pass | {'index': 'e\\1020\\解释\\receipt-check-v1020\\randomized_holdout_publication_receipt_index_receipt_index_receipt_check_v1020.json', 'rows': ['e\\1020\\解释\\receipt-check-v1020\\randomized_holdout_publication_receipt_index_receipt_index_receipt_check_v1020.json']} | source receipt contract check must still exist |
| source_review_file_exists | pass | ['e\\1018\\解释\\receipt-index-review-v1018\\randomized_holdout_publication_receipt_index_receipt_index_review_v1018.json'] | source review must still exist |
| source_receipt_index_file_exists | pass | ['e\\1017\\解释\\receipt-index-v1017\\randomized_holdout_publication_receipt_index_receipt_index_v1017.json'] | source receipt index must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | receipt index review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021 | source receipt index must route to review |

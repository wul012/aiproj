# MiniGPT randomized holdout publication registry lookup index

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_lookup_index_ready`
- Index ready: `True`
- Lookup ready: `True`
- Contract check ready: `True`
- Promotion ready: `False`
- Rejected use: `production_promotion`
- Evidence count: `2`
- Next step: `review_randomized_holdout_publication_registry_lookup_index`

## Lookup Entries

| Lookup key | Entry | Status | Bounded | Promotion | Boundary | Claim |
| --- | --- | --- | --- | --- | --- | --- |
| publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | registered | True | False | governance_lookup_only | bounded_randomized_target_hidden_holdout_claim_only |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| lookup_packet_file_exists | pass | e\934\解释\randomized-holdout-publication-registry-lookup-packet\randomized_holdout_publication_registry_lookup_packet.json | lookup packet file must exist |
| lookup_packet_check_file_exists | pass | e\935\解释\randomized-holdout-publication-registry-lookup-packet-check\randomized_holdout_publication_registry_lookup_packet_check.json | lookup packet check file must exist |
| lookup_packet_passed | pass | pass | lookup packet must pass |
| lookup_packet_decision_ready | pass | randomized_holdout_publication_registry_lookup_packet_ready | lookup packet decision must be ready |
| lookup_packet_summary_ready | pass | {'summary': True, 'packet': True} | lookup packet summary and body must be ready |
| lookup_packet_check_passed | pass | pass | lookup packet check must pass |
| lookup_packet_check_decision_ready | pass | randomized_holdout_publication_registry_lookup_packet_contract_check_passed | lookup packet check decision must pass |
| contract_check_ready | pass | True | lookup packet contract check must be ready |
| lookup_keys_match_check | pass | {'packet': ['publication:randomized-holdout-publication-v928'], 'original': ['publication:randomized-holdout-publication-v928'], 'rebuilt': ['publication:randomized-holdout-publication-v928']} | lookup keys must match the contract check |
| lookup_scope_governance | pass | {'packet': 'governance_lookup_only', 'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | lookup scope must remain governance only |
| lookup_ready | pass | {'packet': True, 'original': True, 'rebuilt': True} | lookup must be ready in packet and check |
| entries_present | pass | {'summary': 1, 'entries': 1} | lookup index requires at least one entry |
| entries_not_promoted | pass | [False] | lookup entries must not be promoted |
| consumer_boundary_governance | pass | governance_lookup_only | consumer boundary must remain governance lookup only |
| rejected_use_production_promotion | pass | {'packet': 'production_promotion', 'original': 'production_promotion', 'rebuilt': 'production_promotion'} | production promotion must stay rejected |
| promotion_still_false | pass | {'packet': False, 'original': False, 'rebuilt': False} | lookup index must not enable promotion |
| source_packet_checks_clean | pass | 0 | source lookup packet checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |

# MiniGPT randomized holdout publication registry packet

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_packet_ready`
- Packet ready: `True`
- Handoff: `ready_for_publication_registry_manifest`
- Entry id: `randomized-holdout-publication-v928`
- Registry status: `registered`
- Contract check: `True`
- Boundary: `governance_lookup_only`
- Next step: `build_randomized_holdout_publication_registry_manifest`

## Evidence

| Kind | Exists | Path |
| --- | --- | --- |
| registry_entry | True | e\929\解释\randomized-holdout-publication-registry-entry\randomized_holdout_publication_registry_entry.json |
| registry_entry_contract_check | True | e\930\解释\randomized-holdout-publication-registry-entry-check\randomized_holdout_publication_registry_entry_check.json |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| evidence_files_exist | pass | [{'kind': 'registry_entry', 'path': 'e\\929\\解释\\randomized-holdout-publication-registry-entry\\randomized_holdout_publication_registry_entry.json', 'exists': True}, {'kind': 'registry_entry_contract_check', 'path': 'e\\930\\解释\\randomized-holdout-publication-registry-entry-check\\randomized_holdout_publication_registry_entry_check.json', 'exists': True}] | registry packet evidence files must exist |
| entry_passed | pass | pass | registry entry must pass |
| entry_ready_decision | pass | randomized_holdout_publication_registry_entry_ready | registry entry decision must be ready |
| entry_summary_ready | pass | True | registry entry summary must be ready |
| entry_registered | pass | registered | registry entry must be registered |
| contract_check_passed | pass | pass | registry entry contract check must pass |
| contract_check_decision_passed | pass | randomized_holdout_publication_registry_entry_contract_check_passed | contract check decision must pass |
| contract_check_ready | pass | True | contract check summary must be ready |
| entry_id_matches_check | pass | {'entry': 'randomized-holdout-publication-v928', 'original': 'randomized-holdout-publication-v928', 'rebuilt': 'randomized-holdout-publication-v928'} | entry id must match original and rebuilt check values |
| bounded_publication_accepted | pass | {'entry': True, 'original': True, 'rebuilt': True} | packet only accepts bounded publication-ready entries |
| consumer_boundary_governance | pass | {'entry': 'governance_lookup_only', 'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| allowed_use_bounded | pass | bounded_model_capability_governance_only | allowed use must stay bounded governance only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must stay bounded |
| promotion_still_false | pass | False | packet must not enable direct promotion |
| approved_for_promotion_false | pass | False | packet must not approve direct promotion |
| source_checks_clean | pass | {'entry': 0, 'check': 0} | entry and contract check must have no failed checks |

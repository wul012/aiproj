# MiniGPT randomized holdout publication registry manifest

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_manifest_ready`
- Manifest ready: `True`
- Manifest id: `randomized-holdout-publication-registry-manifest-v932`
- Entry count: `1`
- Registry status: `registered`
- Boundary: `governance_lookup_only`
- Next step: `review_randomized_holdout_publication_registry_manifest`

## Entries

| Entry | Status | Bounded | Promotion | Boundary | Claim |
| --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-v928 | registered | True | False | governance_lookup_only | bounded_randomized_target_hidden_holdout_claim_only |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| registry_packet_file_exists | pass | e\931\解释\randomized-holdout-publication-registry-packet\randomized_holdout_publication_registry_packet.json | registry packet file must exist |
| registry_packet_passed | pass | pass | registry packet must pass |
| registry_packet_decision_ready | pass | randomized_holdout_publication_registry_packet_ready | registry packet decision must be ready |
| packet_summary_ready | pass | {'summary': True, 'packet': True} | registry packet summary and body must be ready |
| handoff_manifest_ready | pass | ready_for_publication_registry_manifest | packet must route to registry manifest |
| registry_status_registered | pass | registered | manifest only accepts registered entries |
| contract_check_ready | pass | True | packet must carry a ready contract check |
| bounded_publication_accepted | pass | True | manifest only accepts bounded publication entries |
| consumer_boundary_governance | pass | governance_lookup_only | consumer boundary must remain governance lookup only |
| allowed_use_bounded | pass | bounded_model_capability_governance_only | allowed use must stay bounded governance only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must stay bounded |
| promotion_still_false | pass | False | manifest must not enable direct promotion |
| approved_for_promotion_false | pass | False | manifest must not approve direct promotion |
| evidence_count | pass | 2 | manifest expects registry entry and contract check evidence |
| source_checks_clean | pass | 0 | source packet checks must be clean |
| source_next_step_matches | pass | build_randomized_holdout_publication_registry_manifest | source packet must route to registry manifest build |

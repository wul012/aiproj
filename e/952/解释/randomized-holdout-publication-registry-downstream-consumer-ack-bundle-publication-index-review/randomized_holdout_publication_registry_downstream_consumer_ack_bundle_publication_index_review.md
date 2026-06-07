# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication index review

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review_ready`
- Review ready: `True`
- Review status: `approved_for_downstream_publication_lookup_only`
- Consumer: `publication_registry_governance_lookup_reader`
- Publication rows: `1`
- Source evidence: `2`
- Downstream ready: `True`
- Allowed use: `downstream_governance_lookup_only`
- Promotion ready: `False`
- Next step: `record_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt`

## Source

- Publication index: `e\951\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index.json`
- Source publication: `e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.json`
- Source publication check: `e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| publication_index_file_exists | pass | e\951\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index.json | publication index file must exist |
| publication_index_passed | pass | pass | publication index must pass |
| publication_index_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_ready | publication index decision must be ready |
| publication_index_summary_ready | pass | {'summary': True, 'index': True} | publication index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| published_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | published use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | publication index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | publication index must include a ready contract check |
| publication_rows_present | pass | {'rows': 1, 'summary': 1} | publication index review requires one publication row |
| lookup_keys_present | pass | ['publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949'] | lookup keys must use the publication namespace |
| publication_rows_not_promoted | pass | [False] | publication index review must not promote rows |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | publication index review requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_files_exist | pass | ['e\\945\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack\\randomized_holdout_publication_registry_downstream_consumer_ack.json', 'e\\946\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-check\\randomized_holdout_publication_registry_downstream_consumer_ack_check.json'] | source evidence files must exist |
| source_publication_file_exists | pass | e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.json | source publication contract check must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | publication index review must not enable promotion |
| source_checks_clean | pass | 0 | source publication index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index | source publication index must route to review |

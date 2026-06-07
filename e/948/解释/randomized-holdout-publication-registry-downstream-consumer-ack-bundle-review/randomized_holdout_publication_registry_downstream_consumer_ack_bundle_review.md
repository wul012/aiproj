# MiniGPT randomized holdout publication registry downstream consumer ack bundle review

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready`
- Review ready: `True`
- Review status: `approved_for_downstream_consumer_ack_bundle_publication`
- Publish ready: `True`
- Acked use: `downstream_governance_lookup_only`
- Evidence count: `2`
- Promotion ready: `False`
- Next step: `publish_randomized_holdout_publication_registry_downstream_consumer_ack_bundle`

## Evidence

| Kind | Path | SHA-256 | Status | Decision | Failed |
| --- | --- | --- | --- | --- | --- |
| downstream_consumer_ack | e\945\解释\randomized-holdout-publication-registry-downstream-consumer-ack\randomized_holdout_publication_registry_downstream_consumer_ack.json | 4ec43e80fc74b65635773efeb4c7673e57a7ab04eed96e97a3b563c047128695 | pass | randomized_holdout_publication_registry_downstream_consumer_ack_ready | 0 |
| downstream_consumer_ack_contract_check | e\946\解释\randomized-holdout-publication-registry-downstream-consumer-ack-check\randomized_holdout_publication_registry_downstream_consumer_ack_check.json | 5afb49a5007b9ecb71abb92febae5cf8ea117651aa4809fe152d334c309fc39c | pass | randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed | 0 |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| ack_bundle_file_exists | pass | e\947\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle\randomized_holdout_publication_registry_downstream_consumer_ack_bundle.json | ack bundle file must exist |
| ack_bundle_passed | pass | pass | ack bundle must pass |
| ack_bundle_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_ready | ack bundle decision must be ready |
| ack_bundle_summary_ready | pass | {'summary': True, 'bundle': True} | ack bundle summary and body must be ready |
| bundle_status_ready | pass | {'summary': 'ready_for_downstream_consumer_ack_review', 'bundle': 'ready_for_downstream_consumer_ack_review'} | bundle status must route to review |
| evidence_count | pass | {'summary': 2, 'rows': 2} | review requires ack and contract-check evidence |
| evidence_kinds | pass | ['downstream_consumer_ack', 'downstream_consumer_ack_contract_check'] | evidence kinds must remain ordered and complete |
| evidence_files_exist | pass | ['e\\945\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack\\randomized_holdout_publication_registry_downstream_consumer_ack.json', 'e\\946\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-check\\randomized_holdout_publication_registry_downstream_consumer_ack_check.json'] | evidence files must exist |
| evidence_digests_match | pass | ['4ec43e80fc74b65635773efeb4c7673e57a7ab04eed96e97a3b563c047128695', '5afb49a5007b9ecb71abb92febae5cf8ea117651aa4809fe152d334c309fc39c'] | evidence SHA-256 values must match current files |
| evidence_statuses_pass | pass | ['pass', 'pass'] | all evidence rows must pass |
| evidence_failed_counts_zero | pass | [0, 0] | all evidence failed counts must be zero |
| acked_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'bundle': 'downstream_governance_lookup_only'} | acked use must remain downstream lookup only |
| lookup_ready | pass | {'summary': True, 'bundle': True} | bundle review requires lookup-ready bundle |
| contract_check_ready | pass | {'summary': True, 'bundle': True} | bundle review requires contract-ready bundle |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'bundle': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'bundle': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'bundle': False, 'approved': False} | bundle review must not enable promotion |
| source_checks_clean | pass | 0 | source bundle checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle | source bundle must route to review |

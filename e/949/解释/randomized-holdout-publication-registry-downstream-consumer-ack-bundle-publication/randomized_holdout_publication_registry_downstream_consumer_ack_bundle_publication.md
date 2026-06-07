# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready`
- Publication ready: `True`
- Publication status: `published_for_downstream_consumer_lookup_only`
- Published use: `downstream_governance_lookup_only`
- Evidence count: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication`

## Source

- Bundle review: `e\948\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.json`
- Ack bundle: `e\947\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle\randomized_holdout_publication_registry_downstream_consumer_ack_bundle.json`

## Evidence

| Kind | Path | SHA-256 | Status | Decision | Failed |
| --- | --- | --- | --- | --- | --- |
| downstream_consumer_ack | e\945\解释\randomized-holdout-publication-registry-downstream-consumer-ack\randomized_holdout_publication_registry_downstream_consumer_ack.json | 4ec43e80fc74b65635773efeb4c7673e57a7ab04eed96e97a3b563c047128695 | pass | randomized_holdout_publication_registry_downstream_consumer_ack_ready | 0 |
| downstream_consumer_ack_contract_check | e\946\解释\randomized-holdout-publication-registry-downstream-consumer-ack-check\randomized_holdout_publication_registry_downstream_consumer_ack_check.json | 5afb49a5007b9ecb71abb92febae5cf8ea117651aa4809fe152d334c309fc39c | pass | randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed | 0 |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| ack_bundle_review_file_exists | pass | e\948\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.json | ack bundle review file must exist |
| ack_bundle_review_passed | pass | pass | ack bundle review must pass |
| ack_bundle_review_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review_ready | ack bundle review decision must be ready |
| ack_bundle_review_summary_ready | pass | {'summary': True, 'review': True} | ack bundle review summary and body must be ready |
| ack_bundle_file_exists | pass | e\947\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle\randomized_holdout_publication_registry_downstream_consumer_ack_bundle.json | reviewed ack bundle must still exist |
| review_status_publishable | pass | {'summary': 'approved_for_downstream_consumer_ack_bundle_publication', 'review': 'approved_for_downstream_consumer_ack_bundle_publication'} | review must approve lookup-only publication |
| publish_ready | pass | {'summary': True, 'review': True} | publication requires publish-ready review |
| lookup_ready | pass | {'summary': True, 'review': True} | publication requires lookup-ready review |
| contract_check_ready | pass | {'summary': True, 'review': True} | publication requires contract-ready review |
| evidence_count | pass | {'summary': 2, 'rows': 2} | publication requires two evidence rows |
| evidence_kinds | pass | ['downstream_consumer_ack', 'downstream_consumer_ack_contract_check'] | publication evidence kinds must remain ordered and complete |
| evidence_files_exist | pass | ['e\\945\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack\\randomized_holdout_publication_registry_downstream_consumer_ack.json', 'e\\946\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-check\\randomized_holdout_publication_registry_downstream_consumer_ack_check.json'] | publication evidence files must exist |
| evidence_statuses_pass | pass | ['pass', 'pass'] | publication evidence rows must pass |
| acked_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | publication must remain downstream lookup only |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | publication must not enable promotion |
| source_checks_clean | pass | 0 | source review checks must be clean |
| source_next_step_matches | pass | publish_randomized_holdout_publication_registry_downstream_consumer_ack_bundle | source review must route to publication |

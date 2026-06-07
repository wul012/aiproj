# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication index

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_ready`
- Index ready: `True`
- Publication index: `randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-v951`
- Consumer: `publication_registry_governance_lookup_reader`
- Lookup scope: `downstream_governance_lookup_only`
- Published use: `downstream_governance_lookup_only`
- Lookup ready: `True`
- Contract check ready: `True`
- Source evidence count: `2`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index`

## Source Artifacts

- Publication: `e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.json`
- Publication check: `e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.json`

## Publication Rows

| Index | Lookup key | Publication | Status | Consumer | Published use | Evidence | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-v951 | publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949 | published_for_downstream_consumer_lookup_only | publication_registry_governance_lookup_reader | downstream_governance_lookup_only | 2 | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status | Decision | Failed |
| --- | --- | --- | --- | --- | --- |
| downstream_consumer_ack | e\945\解释\randomized-holdout-publication-registry-downstream-consumer-ack\randomized_holdout_publication_registry_downstream_consumer_ack.json | 4ec43e80fc74b65635773efeb4c7673e57a7ab04eed96e97a3b563c047128695 | pass | randomized_holdout_publication_registry_downstream_consumer_ack_ready | 0 |
| downstream_consumer_ack_contract_check | e\946\解释\randomized-holdout-publication-registry-downstream-consumer-ack-check\randomized_holdout_publication_registry_downstream_consumer_ack_check.json | 5afb49a5007b9ecb71abb92febae5cf8ea117651aa4809fe152d334c309fc39c | pass | randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed | 0 |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| publication_file_exists | pass | e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.json | publication file must exist |
| publication_check_file_exists | pass | e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.json | publication contract check file must exist |
| publication_passed | pass | pass | publication must pass |
| publication_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready | publication decision must be ready |
| publication_summary_ready | pass | {'summary': True, 'publication': True} | publication summary and body must be ready |
| publication_check_passed | pass | pass | publication contract check must pass |
| publication_check_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_contract_check_passed | publication contract check decision must pass |
| contract_check_ready | pass | True | publication contract check must be ready |
| publication_status_matches_check | pass | {'publication': 'published_for_downstream_consumer_lookup_only', 'original': 'published_for_downstream_consumer_lookup_only', 'rebuilt': 'published_for_downstream_consumer_lookup_only'} | publication status must match the contract check |
| published_use_lookup_only | pass | {'publication': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | published use must stay downstream lookup only |
| lookup_ready | pass | True | publication index requires lookup-ready publication |
| evidence_count_matches_check | pass | {'publication': 2, 'original': 2, 'rebuilt': 2, 'rows': 2} | publication index requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_files_exist | pass | ['e\\945\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack\\randomized_holdout_publication_registry_downstream_consumer_ack.json', 'e\\946\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-check\\randomized_holdout_publication_registry_downstream_consumer_ack_check.json'] | source evidence files must exist |
| consumer_boundary_governance | pass | governance_lookup_only | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'publication': False, 'original': False, 'rebuilt': False} | publication index must not enable promotion |
| source_publication_checks_clean | pass | 0 | source publication checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'publication': 'check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication', 'check': 'index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication'} | source next steps must route to check then index |

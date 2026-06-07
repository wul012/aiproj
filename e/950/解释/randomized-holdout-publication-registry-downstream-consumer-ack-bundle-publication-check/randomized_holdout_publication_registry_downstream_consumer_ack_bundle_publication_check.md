# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication contract check

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_contract_check_passed`
- Contract check ready: `True`
- Source review: `e\948\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.json`
- Original publication status: `published_for_downstream_consumer_lookup_only`
- Rebuilt publication status: `published_for_downstream_consumer_lookup_only`
- Original published use: `downstream_governance_lookup_only`
- Rebuilt published use: `downstream_governance_lookup_only`
- Original evidence count: `2`
- Rebuilt evidence count: `2`
- Original promotion ready: `False`
- Rebuilt promotion ready: `False`
- Next step: `index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_ack_bundle_review_exists | pass | e\948\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.json | source ack bundle review must exist |
| status | pass | {'original': 'pass', 'rebuilt': 'pass'} | status must rebuild exactly |
| decision | pass | {'original': 'randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready', 'rebuilt': 'randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready'} | decision must rebuild exactly |
| failed_count | pass | {'original': 0, 'rebuilt': 0} | failed count must rebuild exactly |
| evidence_rows | pass | evidence_rows | publication evidence rows must rebuild exactly |
| check_rows | pass | check_rows | publication check rows must rebuild exactly |
| summary.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready | pass | {'original': True, 'rebuilt': True} | summary.randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_ready must rebuild exactly |
| summary.publication_id | pass | {'original': 'randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949', 'rebuilt': 'randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949'} | summary.publication_id must rebuild exactly |
| summary.publication_status | pass | {'original': 'published_for_downstream_consumer_lookup_only', 'rebuilt': 'published_for_downstream_consumer_lookup_only'} | summary.publication_status must rebuild exactly |
| summary.consumer_name | pass | {'original': 'publication_registry_governance_lookup_reader', 'rebuilt': 'publication_registry_governance_lookup_reader'} | summary.consumer_name must rebuild exactly |
| summary.published_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | summary.published_use must rebuild exactly |
| summary.publish_ready | pass | {'original': True, 'rebuilt': True} | summary.publish_ready must rebuild exactly |
| summary.lookup_ready | pass | {'original': True, 'rebuilt': True} | summary.lookup_ready must rebuild exactly |
| summary.contract_check_ready | pass | {'original': True, 'rebuilt': True} | summary.contract_check_ready must rebuild exactly |
| summary.evidence_count | pass | {'original': 2, 'rebuilt': 2} | summary.evidence_count must rebuild exactly |
| summary.promotion_ready | pass | {'original': False, 'rebuilt': False} | summary.promotion_ready must rebuild exactly |
| summary.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | summary.approved_for_promotion must rebuild exactly |
| summary.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | summary.consumer_boundary must rebuild exactly |
| summary.model_quality_claim | pass | {'original': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | summary.model_quality_claim must rebuild exactly |
| publication.publication_ready | pass | {'original': True, 'rebuilt': True} | publication.publication_ready must rebuild exactly |
| publication.publication_id | pass | {'original': 'randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949', 'rebuilt': 'randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949'} | publication.publication_id must rebuild exactly |
| publication.publication_status | pass | {'original': 'published_for_downstream_consumer_lookup_only', 'rebuilt': 'published_for_downstream_consumer_lookup_only'} | publication.publication_status must rebuild exactly |
| publication.ack_bundle_review_path | pass | {'original': 'e\\948\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.json', 'rebuilt': 'e\\948\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-review\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_review.json'} | publication.ack_bundle_review_path must rebuild exactly |
| publication.ack_bundle_path | pass | {'original': 'e\\947\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle.json', 'rebuilt': 'e\\947\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-bundle\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle.json'} | publication.ack_bundle_path must rebuild exactly |
| publication.consumer_name | pass | {'original': 'publication_registry_governance_lookup_reader', 'rebuilt': 'publication_registry_governance_lookup_reader'} | publication.consumer_name must rebuild exactly |
| publication.published_use | pass | {'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | publication.published_use must rebuild exactly |
| publication.publish_ready | pass | {'original': True, 'rebuilt': True} | publication.publish_ready must rebuild exactly |
| publication.lookup_ready | pass | {'original': True, 'rebuilt': True} | publication.lookup_ready must rebuild exactly |
| publication.contract_check_ready | pass | {'original': True, 'rebuilt': True} | publication.contract_check_ready must rebuild exactly |
| publication.evidence_rows | pass | {'original': [{'kind': 'downstream_consumer_ack', 'path': 'e\\945\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack\\randomized_holdout_publication_registry_downstream_consumer_ack.json', 'sha256': '4ec43e80fc74b65635773efeb4c7673e57a7ab04eed96e97a3b563c047128695', 'status': 'pass', 'decision': 'randomized_holdout_publication_registry_downstream_consumer_ack_ready', 'failed_count': 0}, {'kind': 'downstream_consumer_ack_contract_check', 'path': 'e\\946\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-check\\randomized_holdout_publication_registry_downstream_consumer_ack_check.json', 'sha256': '5afb49a5007b9ecb71abb92febae5cf8ea117651aa4809fe152d334c309fc39c', 'status': 'pass', 'decision': 'randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed', 'failed_count': 0}], 'rebuilt': [{'kind': 'downstream_consumer_ack', 'path': 'e\\945\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack\\randomized_holdout_publication_registry_downstream_consumer_ack.json', 'sha256': '4ec43e80fc74b65635773efeb4c7673e57a7ab04eed96e97a3b563c047128695', 'status': 'pass', 'decision': 'randomized_holdout_publication_registry_downstream_consumer_ack_ready', 'failed_count': 0}, {'kind': 'downstream_consumer_ack_contract_check', 'path': 'e\\946\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-check\\randomized_holdout_publication_registry_downstream_consumer_ack_check.json', 'sha256': '5afb49a5007b9ecb71abb92febae5cf8ea117651aa4809fe152d334c309fc39c', 'status': 'pass', 'decision': 'randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed', 'failed_count': 0}]} | publication.evidence_rows must rebuild exactly |
| publication.evidence_count | pass | {'original': 2, 'rebuilt': 2} | publication.evidence_count must rebuild exactly |
| publication.promotion_ready | pass | {'original': False, 'rebuilt': False} | publication.promotion_ready must rebuild exactly |
| publication.approved_for_promotion | pass | {'original': False, 'rebuilt': False} | publication.approved_for_promotion must rebuild exactly |
| publication.consumer_boundary | pass | {'original': 'governance_lookup_only', 'rebuilt': 'governance_lookup_only'} | publication.consumer_boundary must rebuild exactly |
| publication.model_quality_claim | pass | {'original': 'bounded_randomized_target_hidden_holdout_claim_only', 'rebuilt': 'bounded_randomized_target_hidden_holdout_claim_only'} | publication.model_quality_claim must rebuild exactly |
| publication.next_step | pass | {'original': 'check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication', 'rebuilt': 'check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication'} | publication.next_step must rebuild exactly |

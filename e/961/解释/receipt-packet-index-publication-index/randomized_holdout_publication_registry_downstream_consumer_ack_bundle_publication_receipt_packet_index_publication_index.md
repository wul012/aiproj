# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_ready`
- Index ready: `True`
- Publication index: `randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-index-v961`
- Lookup scope: `downstream_governance_lookup_only`
- Published use: `downstream_governance_lookup_only`
- Rows: `1`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index`

## Source

- Publication: `e\959\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.json`
- Publication check: `e\960\解释\receipt-packet-index-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.json`
- Source review: `e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json`
- Source index: `e\957\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.json`

## Publication Index Rows

| Index | Lookup key | Publication | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-index-v961 | publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959 | published_for_downstream_receipt_packet_index_lookup_only | downstream_governance_lookup_only | True | False |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| publication_file_exists | pass | e\959\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.json | publication file must exist |
| publication_check_file_exists | pass | e\960\解释\receipt-packet-index-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.json | publication contract check file must exist |
| publication_passed | pass | pass | publication must pass |
| publication_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_ready | publication decision must be ready |
| publication_summary_ready | pass | {'summary': True, 'publication': True} | publication summary and body must be ready |
| publication_check_passed | pass | pass | publication contract check must pass |
| publication_check_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_contract_check_passed | publication contract check decision must pass |
| contract_check_ready | pass | True | publication contract check must be ready |
| publication_status_matches_check | pass | {'publication': 'published_for_downstream_receipt_packet_index_lookup_only', 'original': 'published_for_downstream_receipt_packet_index_lookup_only', 'rebuilt': 'published_for_downstream_receipt_packet_index_lookup_only'} | publication status must match check |
| published_use_lookup_only | pass | {'publication': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | published use must stay downstream lookup only |
| lookup_ready | pass | True | publication index requires lookup-ready publication |
| packet_index_row_count | pass | {'publication': 1, 'original': 1, 'rebuilt': 1} | publication index requires one packet index row |
| source_packet_row_count | pass | {'publication': 1, 'original': 1, 'rebuilt': 1} | publication index requires one source packet row |
| source_evidence_count | pass | 2 | publication index requires two source evidence rows |
| source_review_file_exists | pass | e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json | source review must still exist |
| source_index_file_exists | pass | e\957\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.json | source receipt packet index must still exist |
| source_packet_file_exists | pass | e\955\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.json | source receipt packet must still exist |
| source_packet_check_file_exists | pass | e\956\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check.json | source receipt packet check must still exist |
| consumer_boundary_governance | pass | governance_lookup_only | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'publication': False, 'original': False, 'rebuilt': False} | publication index must not enable promotion |
| source_publication_checks_clean | pass | 0 | source publication checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'publication': 'check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication', 'check': 'index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication'} | source next steps must route to check then index |

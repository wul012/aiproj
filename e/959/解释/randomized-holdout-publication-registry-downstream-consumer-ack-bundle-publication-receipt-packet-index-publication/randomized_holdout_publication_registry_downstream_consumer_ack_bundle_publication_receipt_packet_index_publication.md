# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_ready`
- Publication ready: `True`
- Publication status: `published_for_downstream_receipt_packet_index_lookup_only`
- Published use: `downstream_governance_lookup_only`
- Packet index rows: `1`
- Source packet rows: `1`
- Source evidence: `2`
- Promotion ready: `False`
- Next step: `check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication`

## Source

- Receipt packet index review: `e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json`
- Receipt packet index: `e\957\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.json`
- Source receipt packet: `e\955\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.json`
- Source receipt packet check: `e\956\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_packet_index_review_file_exists | pass | e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json | receipt packet index review file must exist |
| receipt_packet_index_review_passed | pass | pass | receipt packet index review must pass |
| receipt_packet_index_review_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review_ready | receipt packet index review decision must be ready |
| receipt_packet_index_review_summary_ready | pass | {'summary': True, 'review': True} | review summary and body must be ready |
| review_status_publishable | pass | {'summary': 'approved_for_downstream_receipt_packet_index_publication', 'review': 'approved_for_downstream_receipt_packet_index_publication'} | review must approve lookup-only publication |
| receipt_packet_index_file_exists | pass | e\957\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.json | reviewed receipt packet index must still exist |
| source_packet_file_exists | pass | e\955\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.json | source receipt packet must still exist |
| source_packet_check_file_exists | pass | e\956\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check.json | source receipt packet check must still exist |
| downstream_ready | pass | {'summary': True, 'review': True} | publication requires downstream-ready review |
| publish_ready | pass | {'summary': True, 'review': True} | publication requires publish-ready review |
| lookup_ready | pass | {'summary': True, 'review': True} | publication requires lookup-ready review |
| contract_check_ready | pass | {'summary': True, 'review': True} | publication requires contract-ready review |
| packet_index_row_count | pass | {'summary': 1, 'review': 1} | publication requires one packet index row |
| source_packet_row_count | pass | {'summary': 1, 'review': 1} | publication requires one source packet row |
| source_evidence_count | pass | {'summary': 2, 'review': 2} | publication requires two source evidence rows |
| allowed_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'review': 'downstream_governance_lookup_only'} | publication must remain downstream lookup only |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'review': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'review': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'review': False, 'approved': False} | publication must not enable promotion |
| source_checks_clean | pass | 0 | source review checks must be clean |
| source_next_step_matches | pass | publish_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index | source review must route to publication |

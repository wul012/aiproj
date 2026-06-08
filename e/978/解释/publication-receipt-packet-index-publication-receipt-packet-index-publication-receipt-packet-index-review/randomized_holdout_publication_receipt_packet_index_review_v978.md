# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication receipt packet index review

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review_ready`
- Review ready: `True`
- Review status: `approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication`
- Consumer: `publication_registry_governance_lookup_reader`
- Receipt packet index rows: `1`
- Source packet rows: `1`
- Source evidence: `2`
- Downstream ready: `True`
- Publish ready: `True`
- Allowed use: `downstream_governance_lookup_only`
- Promotion ready: `False`
- Next step: `publish_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index`

## Source

- Receipt packet index: `e\977\解释\publication-receipt-packet-index-publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index.json`
- Source receipt packet: `e\975\解释\publication-receipt-packet-index-publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.json`
- Source receipt packet check: `e\976\解释\publication-receipt-packet-index-publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_check.json`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_packet_index_file_exists | pass | e\977\解释\publication-receipt-packet-index-publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index.json | receipt packet index file must exist |
| receipt_packet_index_passed | pass | pass | receipt packet index must pass |
| receipt_packet_index_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_ready | receipt packet index decision must be ready |
| receipt_packet_index_summary_ready | pass | {'summary': True, 'index': True} | index summary and body must be ready |
| lookup_scope_downstream | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | lookup scope must remain downstream governance lookup only |
| granted_use_lookup_only | pass | {'summary': 'downstream_governance_lookup_only', 'index': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | {'summary': True, 'index': True} | receipt packet index must be lookup-ready |
| contract_check_ready | pass | {'summary': True, 'index': True} | receipt packet index must include a ready contract check |
| receipt_packet_index_rows_present | pass | {'rows': 1, 'summary': 1} | review requires one receipt packet index row |
| source_packet_rows_present | pass | 1 | review requires one source packet row |
| lookup_keys_present | pass | ['publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-v969'] | lookup keys must use the publication namespace |
| receipt_packet_index_rows_not_promoted | pass | [False] | receipt packet index rows must not promote |
| source_packet_rows_not_promoted | pass | [False] | source packet rows must not promote |
| source_evidence_count | pass | {'summary': 2, 'rows': 2} | review requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_files_exist | pass | ['e\\974\\解释\\publication-receipt-packet-index-publication-receipt-review\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.json', 'e\\973\\解释\\publication-receipt-packet-index-publication-receipt\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.json'] | source evidence files must exist |
| source_packet_file_exists | pass | e\975\解释\publication-receipt-packet-index-publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.json | source receipt packet must still exist |
| source_packet_check_file_exists | pass | e\976\解释\publication-receipt-packet-index-publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_check.json | source receipt packet contract check must still exist |
| consumer_boundary_governance | pass | {'summary': 'governance_lookup_only', 'index': 'governance_lookup_only'} | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | {'summary': 'bounded_randomized_target_hidden_holdout_claim_only', 'index': 'bounded_randomized_target_hidden_holdout_claim_only'} | model quality claim must remain bounded |
| promotion_still_false | pass | {'summary': False, 'index': False, 'approved': False} | review must not enable promotion |
| source_checks_clean | pass | 0 | source receipt packet index checks must be clean |
| source_next_step_matches | pass | review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index | source receipt packet index must route to review |

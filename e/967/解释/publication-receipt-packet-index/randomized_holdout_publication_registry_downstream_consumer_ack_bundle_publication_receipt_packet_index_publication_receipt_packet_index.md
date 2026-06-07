# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_ready`
- Index ready: `True`
- Receipt packet index: `randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-v967`
- Consumer: `publication_registry_governance_lookup_reader`
- Lookup scope: `downstream_governance_lookup_only`
- Granted use: `downstream_governance_lookup_only`
- Lookup ready: `True`
- Contract check ready: `True`
- Source evidence count: `2`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index`

## Source Artifacts

- Receipt packet: `e\965\解释\publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.json`
- Receipt packet check: `e\966\解释\publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.json`

## Receipt Packet Index Rows

| Index | Lookup key | Packet | Status | Consumer | Granted use | Evidence | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-v967 | publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-v965 | downstream_receipt_packet_index_publication_receipt_packet_ready | publication_registry_governance_lookup_reader | downstream_governance_lookup_only | 2 | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| receipt_review | e\964\解释\publication-receipt-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review.json | 776db534a769affb380cb01c310d6a4f04660d0835035827a99e21c8ad9f902a | pass |
| publication_receipt | e\963\解释\publication-index-receipt\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.json | 3f813fa5395fa5f76b27943a2566c37fb848c5564700194eec193e0760fe2db9 | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_packet_file_exists | pass | e\965\解释\publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.json | receipt packet file must exist |
| receipt_packet_check_file_exists | pass | e\966\解释\publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.json | receipt packet contract check file must exist |
| receipt_packet_passed | pass | pass | receipt packet must pass |
| receipt_packet_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_ready | receipt packet decision must be ready |
| receipt_packet_summary_ready | pass | {'summary': True, 'packet': True} | packet summary and body must be ready |
| receipt_packet_check_passed | pass | pass | receipt packet contract check must pass |
| receipt_packet_check_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_contract_check_passed | receipt packet contract check decision must pass |
| contract_check_ready | pass | True | receipt packet contract check must be ready |
| packet_status_matches_check | pass | {'packet': 'downstream_receipt_packet_index_publication_receipt_packet_ready', 'original': 'downstream_receipt_packet_index_publication_receipt_packet_ready', 'rebuilt': 'downstream_receipt_packet_index_publication_receipt_packet_ready'} | packet status must match the contract check |
| granted_use_lookup_only | pass | {'packet': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | True | receipt packet index requires lookup-ready packet |
| packet_rows_present | pass | {'rows': 1, 'summary': 1} | receipt packet index requires one packet row |
| source_evidence_rows_present | pass | {'rows': 2, 'summary': 2} | receipt packet index requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_files_exist | pass | ['e\\964\\解释\\publication-receipt-review\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review.json', 'e\\963\\解释\\publication-index-receipt\\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.json'] | source evidence files must exist |
| lookup_key_namespace | pass | ['publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959'] | packet lookup keys must use publication namespace |
| source_receipt_review_file_exists | pass | e\964\解释\publication-receipt-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review.json | source receipt review must still exist |
| source_publication_receipt_file_exists | pass | e\963\解释\publication-index-receipt\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.json | source publication receipt must still exist |
| source_index_review_file_exists | pass | e\962\解释\receipt-packet-index-publication-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.json | source index review must still exist |
| source_publication_file_exists | pass | e\959\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\960\解释\receipt-packet-index-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.json | source publication contract check must still exist |
| source_review_file_exists | pass | e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.json | source publication review must still exist |
| source_index_file_exists | pass | e\957\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.json | source publication index must still exist |
| consumer_boundary_governance | pass | governance_lookup_only | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'packet': False, 'original': False, 'rebuilt': False} | receipt packet index must not enable promotion |
| source_packet_checks_clean | pass | 0 | source receipt packet checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'packet': 'check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet', 'check': 'index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet'} | source next steps must route to check then index |

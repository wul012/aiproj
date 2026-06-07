# MiniGPT randomized holdout publication registry downstream consumer ack bundle publication receipt packet index

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_ready`
- Index ready: `True`
- Packet index: `randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-v957`
- Consumer: `publication_registry_governance_lookup_reader`
- Lookup scope: `downstream_governance_lookup_only`
- Granted use: `downstream_governance_lookup_only`
- Lookup ready: `True`
- Contract check ready: `True`
- Source evidence count: `2`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index`

## Source Artifacts

- Receipt packet: `e\955\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.json`
- Receipt packet check: `e\956\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check.json`

## Packet Index Rows

| Index | Lookup key | Packet | Status | Consumer | Granted use | Evidence | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-v957 | publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-v955 | downstream_publication_receipt_packet_ready | publication_registry_governance_lookup_reader | downstream_governance_lookup_only | 2 | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status | Decision | Failed |
| --- | --- | --- | --- | --- | --- |
| downstream_consumer_ack | e\945\解释\randomized-holdout-publication-registry-downstream-consumer-ack\randomized_holdout_publication_registry_downstream_consumer_ack.json | 4ec43e80fc74b65635773efeb4c7673e57a7ab04eed96e97a3b563c047128695 | pass | randomized_holdout_publication_registry_downstream_consumer_ack_ready | 0 |
| downstream_consumer_ack_contract_check | e\946\解释\randomized-holdout-publication-registry-downstream-consumer-ack-check\randomized_holdout_publication_registry_downstream_consumer_ack_check.json | 5afb49a5007b9ecb71abb92febae5cf8ea117651aa4809fe152d334c309fc39c | pass | randomized_holdout_publication_registry_downstream_consumer_ack_contract_check_passed | 0 |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| receipt_packet_file_exists | pass | e\955\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.json | receipt packet file must exist |
| receipt_packet_check_file_exists | pass | e\956\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check.json | receipt packet contract check file must exist |
| receipt_packet_passed | pass | pass | receipt packet must pass |
| receipt_packet_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_ready | receipt packet decision must be ready |
| receipt_packet_summary_ready | pass | {'summary': True, 'packet': True} | packet summary and body must be ready |
| receipt_packet_check_passed | pass | pass | receipt packet contract check must pass |
| receipt_packet_check_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_contract_check_passed | receipt packet contract check decision must pass |
| contract_check_ready | pass | True | receipt packet contract check must be ready |
| packet_status_matches_check | pass | {'packet': 'downstream_publication_receipt_packet_ready', 'original': 'downstream_publication_receipt_packet_ready', 'rebuilt': 'downstream_publication_receipt_packet_ready'} | packet status must match the contract check |
| granted_use_lookup_only | pass | {'packet': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| lookup_ready | pass | True | receipt packet index requires lookup-ready packet |
| packet_rows_present | pass | {'rows': 1, 'summary': 1} | receipt packet index requires one packet row |
| source_evidence_rows_present | pass | {'rows': 2, 'summary': 2} | receipt packet index requires two source evidence rows |
| source_evidence_passed | pass | ['pass', 'pass'] | source evidence rows must pass |
| source_evidence_files_exist | pass | ['e\\945\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack\\randomized_holdout_publication_registry_downstream_consumer_ack.json', 'e\\946\\解释\\randomized-holdout-publication-registry-downstream-consumer-ack-check\\randomized_holdout_publication_registry_downstream_consumer_ack_check.json'] | source evidence files must exist |
| lookup_key_namespace | pass | ['publication:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-v949'] | packet lookup keys must use publication namespace |
| source_receipt_review_file_exists | pass | e\954\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review.json | source receipt review must still exist |
| source_publication_receipt_file_exists | pass | e\953\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt.json | source publication receipt must still exist |
| source_index_review_file_exists | pass | e\952\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_index_review.json | source index review must still exist |
| source_publication_file_exists | pass | e\949\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication.json | source publication must still exist |
| source_publication_check_file_exists | pass | e\950\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_check.json | source publication contract check must still exist |
| consumer_boundary_governance | pass | governance_lookup_only | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'packet': False, 'original': False, 'rebuilt': False} | receipt packet index must not enable promotion |
| source_packet_checks_clean | pass | 0 | source receipt packet checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'packet': 'check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet', 'check': 'index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet'} | source next steps must route to check then index |

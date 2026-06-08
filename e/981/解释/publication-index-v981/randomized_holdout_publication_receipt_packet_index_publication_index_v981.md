# MiniGPT randomized holdout publication receipt packet index publication index v981

- Status: `pass`
- Decision: `randomized_holdout_publication_receipt_packet_index_publication_index_v981_ready`
- Index ready: `True`
- Publication index: `randomized-holdout-publication-receipt-packet-index-publication-index-v981`
- Lookup scope: `downstream_governance_lookup_only`
- Lookup key count: `1`
- Publication status: `published_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_lookup_only`
- Published use: `downstream_governance_lookup_only`
- Contract check ready: `True`
- Promotion ready: `False`
- Next step: `review_randomized_holdout_publication_receipt_packet_index_publication_index_v981`

## Source Artifacts

- Publication: `e\979\解释\publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication\randomized_holdout_publication_receipt_packet_index_publication_v979.json`
- Publication check: `e\980\解释\publication-receipt-packet-index-publication-check\randomized_holdout_publication_receipt_packet_index_publication_check_v980.json`

## Publication Index Rows

| Index | Lookup key | Publication | Status | Use | Contract | Promotion |
| --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-receipt-packet-index-publication-index-v981 | publication-index:randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication-v979 | randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication-v979 | published_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_lookup_only | downstream_governance_lookup_only | True | False |

## Source Evidence

| Kind | Path | SHA-256 | Status |
| --- | --- | --- | --- |
| publication | e\979\解释\publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication\randomized_holdout_publication_receipt_packet_index_publication_v979.json | d3090ee99402c69e45c7bcbc91410c6d57db3c8c6676adc7d41ec3ce89cdb180 | pass |
| publication_check | e\980\解释\publication-receipt-packet-index-publication-check\randomized_holdout_publication_receipt_packet_index_publication_check_v980.json | 3ef37eee2165c5d61f61b10b3081e8ba357d4af0599708a0fe68f1980793ad6a | pass |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| publication_file_exists | pass | e\979\解释\publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-publication\randomized_holdout_publication_receipt_packet_index_publication_v979.json | publication file must exist |
| publication_check_file_exists | pass | e\980\解释\publication-receipt-packet-index-publication-check\randomized_holdout_publication_receipt_packet_index_publication_check_v980.json | publication contract check file must exist |
| publication_passed | pass | pass | publication must pass |
| publication_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication_ready | publication decision must be ready |
| publication_summary_ready | pass | {'summary': 'published_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_lookup_only', 'publication': True} | publication summary and body must be lookup-only ready |
| publication_check_passed | pass | pass | publication contract check must pass |
| publication_check_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication_contract_check_passed | publication contract check decision must pass |
| contract_check_ready | pass | True | publication contract check must be ready |
| publication_status_matches_check | pass | {'publication': 'published_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_lookup_only', 'original': 'published_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_lookup_only', 'rebuilt': 'published_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_lookup_only'} | publication status must match rebuilt check |
| published_use_lookup_only | pass | {'publication': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | published use must stay downstream lookup only |
| lookup_ready | pass | True | publication index requires lookup-ready publication |
| publication_contract_ready | pass | {'publication': True, 'check': True} | publication and check must both be contract-ready |
| receipt_packet_index_rows | pass | {'publication': 1, 'original': 1, 'rebuilt': 1} | publication index requires one receipt packet index row |
| source_packet_rows | pass | {'publication': 1, 'original': 1, 'rebuilt': 1} | publication index requires one source packet row |
| source_evidence_count | pass | 2 | publication index requires two source evidence rows |
| source_review_file_exists | pass | e\978\解释\publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-review\randomized_holdout_publication_receipt_packet_index_review_v978.json | source receipt packet index review must still exist |
| source_index_file_exists | pass | e\977\解释\publication-receipt-packet-index-publication-receipt-packet-index\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index.json | source receipt packet index must still exist |
| source_packet_file_exists | pass | e\975\解释\publication-receipt-packet-index-publication-receipt-packet\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.json | source packet must still exist |
| source_packet_check_file_exists | pass | e\976\解释\publication-receipt-packet-index-publication-receipt-packet-check\randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_check.json | source packet check must still exist |
| consumer_boundary_governance | pass | governance_lookup_only | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'publication': False, 'approved': False, 'original': False, 'rebuilt': False} | publication index must not enable promotion |
| source_publication_checks_clean | pass | 0 | source publication checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |
| source_next_steps_match | pass | {'publication': 'check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication', 'check': 'index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication'} | source next steps must route to check then index |

# MiniGPT randomized holdout publication registry downstream consumer index

- Status: `pass`
- Decision: `randomized_holdout_publication_registry_downstream_consumer_index_ready`
- Index ready: `True`
- Consumer index: `randomized-holdout-publication-registry-downstream-consumer-index-v943`
- Consumer: `publication_registry_governance_lookup_reader`
- Lookup scope: `downstream_governance_lookup_only`
- Lookup ready: `True`
- Contract check ready: `True`
- Granted use: `downstream_governance_lookup_only`
- Promotion ready: `False`
- Blocked uses: `['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']`
- Evidence count: `2`
- Next step: `review_randomized_holdout_publication_registry_downstream_consumer_index`

## Source Evidence

- Consumer packet: `e\941\解释\randomized-holdout-publication-registry-downstream-consumer-packet\randomized_holdout_publication_registry_downstream_consumer_packet.json`
- Consumer packet check: `e\942\解释\randomized-holdout-publication-registry-downstream-consumer-packet-check\randomized_holdout_publication_registry_downstream_consumer_packet_check.json`

## Lookup Rows

| Index | Consumer | Lookup key | Entry | Granted use | Blocked uses | Promotion | Contract check |
| --- | --- | --- | --- | --- | --- | --- | --- |
| randomized-holdout-publication-registry-downstream-consumer-index-v943 | publication_registry_governance_lookup_reader | publication:randomized-holdout-publication-v928 | randomized-holdout-publication-v928 | downstream_governance_lookup_only | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | False | True |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| consumer_packet_file_exists | pass | e\941\解释\randomized-holdout-publication-registry-downstream-consumer-packet\randomized_holdout_publication_registry_downstream_consumer_packet.json | consumer packet file must exist |
| consumer_packet_check_file_exists | pass | e\942\解释\randomized-holdout-publication-registry-downstream-consumer-packet-check\randomized_holdout_publication_registry_downstream_consumer_packet_check.json | consumer packet check file must exist |
| consumer_packet_passed | pass | pass | consumer packet must pass |
| consumer_packet_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_packet_ready | consumer packet decision must be ready |
| consumer_packet_summary_ready | pass | {'summary': True, 'packet': True} | consumer packet summary and body must be ready |
| consumer_packet_check_passed | pass | pass | consumer packet check must pass |
| consumer_packet_check_decision_ready | pass | randomized_holdout_publication_registry_downstream_consumer_packet_contract_check_passed | consumer packet check decision must pass |
| contract_check_ready | pass | True | consumer packet contract check must be ready |
| lookup_keys_match_check | pass | {'packet': ['publication:randomized-holdout-publication-v928'], 'original': ['publication:randomized-holdout-publication-v928'], 'rebuilt': ['publication:randomized-holdout-publication-v928']} | lookup keys must match the contract check |
| lookup_ready | pass | True | consumer index requires lookup-ready packet |
| granted_use_lookup_only | pass | {'packet': 'downstream_governance_lookup_only', 'original': 'downstream_governance_lookup_only', 'rebuilt': 'downstream_governance_lookup_only'} | granted use must stay downstream lookup only |
| blocked_uses_complete | pass | ['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion'] | consumer index must preserve all blocked uses |
| packet_rows_present | pass | {'packet_rows': 1, 'entry_count': 1} | consumer index requires packet rows |
| packet_rows_not_promoted | pass | [False] | packet rows must not be promoted |
| consumer_boundary_governance | pass | governance_lookup_only | consumer boundary must remain governance lookup only |
| model_quality_claim_bounded | pass | bounded_randomized_target_hidden_holdout_claim_only | model quality claim must remain bounded |
| promotion_still_false | pass | {'packet': False, 'original': False, 'rebuilt': False} | consumer index must not enable promotion |
| source_packet_checks_clean | pass | 0 | source consumer packet checks must be clean |
| source_contract_checks_clean | pass | 0 | source contract checks must be clean |

# MiniGPT Artifact Schema Guard

- Generated: `2026-07-07T05:09:08Z`
- Status: `pass`
- Decision: `continue_with_artifact_schema_guard`
- Registry: `docs/artifact-schema-guard-registry.json`

## Summary

| Metric | Value |
| --- | --- |
| schema_count | 4 |
| artifact_count | 4 |
| check_count | 125 |
| passed_check_count | 125 |
| failed_check_count | 0 |

## Checks

| Schema | Artifact | Check | Expected | Actual | Status |
| --- | --- | --- | --- | --- | --- |
| registry |  | schema_version | 1 | 1 | pass |
| registry |  | scope | cards_and_publication_receipts | cards_and_publication_receipts | pass |
| registry |  | schemas_present | non-empty list | 4 | pass |
| experiment_card_v1 |  | schema_id_present | non-empty unique id | experiment_card_v1 | pass |
| experiment_card_v1 |  | artifact_kind_present | non-empty | experiment_card | pass |
| experiment_card_v1 |  | required_fields_present | non-empty list | 13 | pass |
| experiment_card_v1 |  | artifact_paths_present | non-empty list | 1 | pass |
| experiment_card_v1 |  | type_rule:summary | known type | dict | pass |
| experiment_card_v1 |  | type_rule:artifacts | known type | list | pass |
| experiment_card_v1 |  | type_rule:recommendations | known type | list | pass |
| experiment_card_v1 |  | type_rule:warnings | known type | list | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | artifact_exists | exists inside project | f/1265/解释/schema-samples/experiment-card/experiment_card.json | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:schema_version | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:title | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:generated_at | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:run_dir | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:summary | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:notes | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:data | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:training | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:evaluation | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:registry | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:artifacts | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:recommendations | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | field:warnings | present | present | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | value:schema_version | 1 | 1 | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | type:summary | dict | dict | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | type:artifacts | list | list | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | type:recommendations | list | list | pass |
| experiment_card_v1 | f/1265/解释/schema-samples/experiment-card/experiment_card.json | type:warnings | list | list | pass |
| dataset_card_v1 |  | schema_id_present | non-empty unique id | dataset_card_v1 | pass |
| dataset_card_v1 |  | artifact_kind_present | non-empty | dataset_card | pass |
| dataset_card_v1 |  | required_fields_present | non-empty list | 14 | pass |
| dataset_card_v1 |  | artifact_paths_present | non-empty list | 1 | pass |
| dataset_card_v1 |  | type_rule:dataset | known type | dict | pass |
| dataset_card_v1 |  | type_rule:summary | known type | dict | pass |
| dataset_card_v1 |  | type_rule:intended_use | known type | list | pass |
| dataset_card_v1 |  | type_rule:limitations | known type | list | pass |
| dataset_card_v1 |  | type_rule:artifacts | known type | list | pass |
| dataset_card_v1 |  | type_rule:recommendations | known type | list | pass |
| dataset_card_v1 |  | type_rule:warnings | known type | list | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | artifact_exists | exists inside project | f/1265/解释/schema-samples/dataset-card/dataset_card.json | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:schema_version | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:title | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:generated_at | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:dataset_dir | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:dataset | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:summary | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:intended_use | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:limitations | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:provenance | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:snapshot | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:quality | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:artifacts | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:recommendations | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | field:warnings | present | present | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | value:schema_version | 1 | 1 | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | type:dataset | dict | dict | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | type:summary | dict | dict | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | type:intended_use | list | list | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | type:limitations | list | list | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | type:artifacts | list | list | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | type:recommendations | list | list | pass |
| dataset_card_v1 | f/1265/解释/schema-samples/dataset-card/dataset_card.json | type:warnings | list | list | pass |
| model_card_v1 |  | schema_id_present | non-empty unique id | model_card_v1 | pass |
| model_card_v1 |  | artifact_kind_present | non-empty | model_card | pass |
| model_card_v1 |  | required_fields_present | non-empty list | 11 | pass |
| model_card_v1 |  | artifact_paths_present | non-empty list | 1 | pass |
| model_card_v1 |  | type_rule:summary | known type | dict | pass |
| model_card_v1 |  | type_rule:intended_use | known type | list | pass |
| model_card_v1 |  | type_rule:limitations | known type | list | pass |
| model_card_v1 |  | type_rule:coverage | known type | dict | pass |
| model_card_v1 |  | type_rule:runs | known type | list | pass |
| model_card_v1 |  | type_rule:recommendations | known type | list | pass |
| model_card_v1 |  | type_rule:warnings | known type | list | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | artifact_exists | exists inside project | f/1265/解释/schema-samples/model-card/model_card.json | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:schema_version | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:title | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:generated_at | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:registry_path | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:summary | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:intended_use | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:limitations | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:coverage | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:runs | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:recommendations | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | field:warnings | present | present | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | value:schema_version | 1 | 1 | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | type:summary | dict | dict | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | type:intended_use | list | list | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | type:limitations | list | list | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | type:coverage | dict | dict | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | type:runs | list | list | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | type:recommendations | list | list | pass |
| model_card_v1 | f/1265/解释/schema-samples/model-card/model_card.json | type:warnings | list | list | pass |
| publication_receipt_v1 |  | schema_id_present | non-empty unique id | publication_receipt_v1 | pass |
| publication_receipt_v1 |  | artifact_kind_present | non-empty | publication_receipt | pass |
| publication_receipt_v1 |  | required_fields_present | non-empty list | 9 | pass |
| publication_receipt_v1 |  | artifact_paths_present | non-empty list | 1 | pass |
| publication_receipt_v1 |  | type_rule:receipt | known type | dict | pass |
| publication_receipt_v1 |  | type_rule:summary | known type | dict | pass |
| publication_receipt_v1 |  | type_rule:interpretation | known type | dict | pass |
| publication_receipt_v1 |  | type_rule:check_rows | known type | list | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | artifact_exists | exists inside project | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | field:schema_version | present | present | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | field:title | present | present | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | field:generated_at | present | present | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | field:status | present | present | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | field:decision | present | present | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | field:receipt | present | present | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | field:summary | present | present | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | field:interpretation | present | present | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | field:check_rows | present | present | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | value:schema_version | 1 | 1 | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | value:status | pass | pass | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | value:summary.granted_use | downstream_governance_lookup_only | downstream_governance_lookup_only | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | value:summary.promotion_ready | False | False | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | value:summary.approved_for_promotion | False | False | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | value:receipt.granted_use | downstream_governance_lookup_only | downstream_governance_lookup_only | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | value:receipt.promotion_ready | False | False | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | value:receipt.approved_for_promotion | False | False | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | type:receipt | dict | dict | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | type:summary | dict | dict | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | type:interpretation | dict | dict | pass |
| publication_receipt_v1 | e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.json | type:check_rows | list | list | pass |

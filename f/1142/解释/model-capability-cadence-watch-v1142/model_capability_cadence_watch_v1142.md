# MiniGPT model capability cadence watch v1142

- Generated: `2026-06-12T05:39:21Z`
- Status: `watch`
- Decision: `model_capability_cadence_ready`

## Summary

| Metric | Value |
| --- | --- |
| status | watch |
| decision | model_capability_cadence_ready |
| scanned_version_count | 12 |
| leading_non_capability_run | 6 |
| max_non_capability_run | 4 |
| latest_model_capability_version | v1136 |
| latest_refactor_version | v1140 |
| versions_since_last_refactor | 2 |
| latest_explanation_version | v1142 |
| versions_since_last_explanation | 0 |
| latest_evidence_version | v1142 |
| versions_since_last_evidence | 0 |
| due_count | 2 |
| due_list | run_selected_model_capability_regression_execution, schedule_model_capability_regression |
| next_action | run_selected_model_capability_regression_execution |
| cadence_ready | True |

## Recent Version Cadence

| version | category | model_signal | governance_signal | maintenance_signal | status | recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| v1142 | maintenance |  |  | maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1141 | maintenance |  |  | maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1140 | refactor |  |  | maintenance | pass | counts as the latest contract-preserving maintenance slot |
| v1139 | maintenance |  |  | maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1138 | maintenance |  |  | maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1137 | maintenance |  |  | maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1136 | model-capability | required term, loss signal, decoder |  | maintenance | pass | keep as cadence anchor |
| v1135 | model-capability | required term, loss signal, decoder |  | maintenance | pass | keep as cadence anchor |
| v1134 | maintenance |  |  | docs, maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1133 | maintenance |  |  | docs, maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1132 | maintenance |  | receipt, publication | docs, template, maintenance, script layer | pass | batch with readability care and schedule model capability follow-up |
| v1131 | maintenance | required term | receipt, publication | readability, docs, maintenance | pass | batch with readability care and schedule model capability follow-up |

## Recommendations

- Leading non-capability run is 6, above the configured limit 4.
- Schedule a focused model capability regression after this maintenance batch.
- Candidate checks: holdout accuracy, required term coverage, loss signal bridge, unassisted repair, or decoder anchor distribution.

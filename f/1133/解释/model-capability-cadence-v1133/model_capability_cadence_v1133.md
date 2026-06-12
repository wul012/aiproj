# MiniGPT model capability cadence v1133

- Generated: `2026-06-12T02:08:38Z`
- Status: `watch`
- Decision: `model_capability_cadence_ready`

## Summary

| Metric | Value |
| --- | --- |
| status | watch |
| decision | model_capability_cadence_ready |
| scanned_version_count | 12 |
| leading_non_capability_run | 12 |
| max_non_capability_run | 4 |
| latest_model_capability_version | not_found_in_recent_window |
| next_action | schedule_model_capability_regression |
| cadence_ready | True |

## Recent Version Cadence

| version | category | model_signal | governance_signal | maintenance_signal | status | recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| v1133 | maintenance |  |  | docs, maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1132 | maintenance |  | receipt, publication | docs, template, maintenance, script layer | pass | batch with readability care and schedule model capability follow-up |
| v1131 | maintenance | required term | receipt, publication | readability, docs, maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1130 | maintenance |  | receipt, index, publication | readability, maintenance | pass | batch with readability care and schedule model capability follow-up |
| v1129 | governance |  | receipt, index, review, lookup-only, publication |  | pass | keep lookup-only boundaries explicit |
| v1128 | governance |  | receipt, index, review, lookup-only, publication |  | pass | keep lookup-only boundaries explicit |
| v1127 | governance |  | receipt, contract check, index, review, lookup-only, publication |  | pass | keep lookup-only boundaries explicit |
| v1126 | governance |  | receipt, index, review, publication |  | pass | keep lookup-only boundaries explicit |
| v1125 | governance |  | receipt, index, review, lookup-only, publication |  | pass | keep lookup-only boundaries explicit |
| v1124 | governance |  | receipt, index, review, lookup-only, publication |  | pass | keep lookup-only boundaries explicit |
| v1123 | governance |  | receipt, contract check, index, review, lookup-only, publication |  | pass | keep lookup-only boundaries explicit |
| v1122 | governance |  | receipt, index, review, publication |  | pass | keep lookup-only boundaries explicit |

## Recommendations

- Leading non-capability run is 12, above the configured limit 4.
- Schedule a focused model capability regression after this maintenance batch.
- Candidate checks: holdout accuracy, required term coverage, loss signal bridge, unassisted repair, or decoder anchor distribution.

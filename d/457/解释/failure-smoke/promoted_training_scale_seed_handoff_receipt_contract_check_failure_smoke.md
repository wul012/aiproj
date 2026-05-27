# Promoted Receipt Contract Summary-Check Failure Smoke

- Status: `pass`
- Decision: `failure_matrix_verified`
- Scenario count: `4`
- Failed verification count: `0`

## Scenarios

| Scenario | Tamper | Check status | Verification | Failed families | Failed targets |
| --- | --- | --- | --- | --- | --- |
| baseline | none | pass | pass | [] | [] |
| tamper_summary_field | receipt_schema_version | fail | pass | ["summary_field"] | ["summary.receipt_schema_version"] |
| tamper_contract_profile | contract_check_type_summary | fail | pass | ["contract_profile", "summary_field"] | ["summary.contract_check_type_summary"] |
| tamper_sidecar | html_sidecar | fail | pass | ["sidecar"] | ["d\\457\\解释\\failure-smoke\\scenarios\\tamper_sidecar\\summary\\promoted_training_scale_seed_handoff_receipt_contract_summary.html"] |

## Issues

- none

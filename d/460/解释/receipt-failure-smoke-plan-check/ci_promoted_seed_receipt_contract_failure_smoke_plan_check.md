# CI promoted seed receipt failure-smoke plan check

- Status: `pass`
- Decision: `continue`
- Source plan: `d\460\解释\receipt-failure-smoke-wrapper\ci_promoted_seed_receipt_contract_failure_smoke_plan.json`
- Source handoff: `d\448\解释\promoted-handoff`

## Checks

| ID | Target | Expected | Actual | Status | Detail |
| --- | --- | --- | --- | --- | --- |
| plan:wrapper | wrapper | run_ci_promoted_seed_receipt_contract_failure_smoke | run_ci_promoted_seed_receipt_contract_failure_smoke | pass | Wrapper identity must remain stable. |
| plan:status | status | pass | pass | pass | Wrapper plan must record a successful run. |
| plan:decision | decision | receipt_contract_failure_smoke_verified | receipt_contract_failure_smoke_verified | pass | Wrapper decision must preserve the verified smoke outcome. |
| command:receipt_contract_summary:present | commands.receipt_contract_summary | True | True | pass | Required child command must be recorded in the wrapper plan. |
| command:receipt_contract_summary:returncode | commands.receipt_contract_summary.returncode | 0 | 0 | pass | Required child command must complete successfully. |
| command:receipt_contract_failure_smoke:present | commands.receipt_contract_failure_smoke | True | True | pass | Required child command must be recorded in the wrapper plan. |
| command:receipt_contract_failure_smoke:returncode | commands.receipt_contract_failure_smoke.returncode | 0 | 0 | pass | Required child command must complete successfully. |
| failure_smoke_summary:available | failure_smoke_summary.available | True | True | pass | Failure-smoke summary must keep the expected verified matrix result. |
| failure_smoke_summary:parse_status | failure_smoke_summary.parse_status | pass | pass | pass | Failure-smoke summary must keep the expected verified matrix result. |
| failure_smoke_summary:status | failure_smoke_summary.status | pass | pass | pass | Failure-smoke summary must keep the expected verified matrix result. |
| failure_smoke_summary:scenario_count | failure_smoke_summary.scenario_count | 4 | 4 | pass | Failure-smoke summary must keep the expected verified matrix result. |
| failure_smoke_summary:verified_scenario_count | failure_smoke_summary.verified_scenario_count | 4 | 4 | pass | Failure-smoke summary must keep the expected verified matrix result. |
| failure_smoke_summary:failed_verification_count | failure_smoke_summary.failed_verification_count | 0 | 0 | pass | Failure-smoke summary must keep the expected verified matrix result. |
| artifact:contract_summary_json:recorded_exists | artifact_digest.contract_summary_json.exists | True | True | pass | Artifact must be recorded as present. |
| artifact:contract_summary_json:current_exists | artifact_digest.contract_summary_json.path | True | True | pass | Recorded artifact path must still exist. |
| artifact:contract_summary_json:size | artifact_digest.contract_summary_json.size_bytes | 25354 | 25354 | pass | Recorded artifact size must match the current file. |
| artifact:contract_summary_json:sha256_shape | artifact_digest.contract_summary_json.sha256 | 64 lowercase hex | 64 lowercase hex | pass | Recorded SHA-256 must be a stable 64-character lowercase hex digest. |
| artifact:contract_summary_json:sha256 | artifact_digest.contract_summary_json.sha256 | 73db95c749effdc39d98b4d41c4dcb583c61d9585f786e7e810a503775128a3f | 73db95c749effdc39d98b4d41c4dcb583c61d9585f786e7e810a503775128a3f | pass | Recorded artifact digest must match the current file. |
| artifact:failure_smoke_json:recorded_exists | artifact_digest.failure_smoke_json.exists | True | True | pass | Artifact must be recorded as present. |
| artifact:failure_smoke_json:current_exists | artifact_digest.failure_smoke_json.path | True | True | pass | Recorded artifact path must still exist. |
| artifact:failure_smoke_json:size | artifact_digest.failure_smoke_json.size_bytes | 6738 | 6738 | pass | Recorded artifact size must match the current file. |
| artifact:failure_smoke_json:sha256_shape | artifact_digest.failure_smoke_json.sha256 | 64 lowercase hex | 64 lowercase hex | pass | Recorded SHA-256 must be a stable 64-character lowercase hex digest. |
| artifact:failure_smoke_json:sha256 | artifact_digest.failure_smoke_json.sha256 | 162e95e66de9c048110ad244e1ae1fc18148ef33a5d5d40b54742d9c57fafa4e | 162e95e66de9c048110ad244e1ae1fc18148ef33a5d5d40b54742d9c57fafa4e | pass | Recorded artifact digest must match the current file. |
| artifact:failure_smoke_csv:recorded_exists | artifact_digest.failure_smoke_csv.exists | True | True | pass | Artifact must be recorded as present. |
| artifact:failure_smoke_csv:current_exists | artifact_digest.failure_smoke_csv.path | True | True | pass | Recorded artifact path must still exist. |
| artifact:failure_smoke_csv:size | artifact_digest.failure_smoke_csv.size_bytes | 983 | 983 | pass | Recorded artifact size must match the current file. |
| artifact:failure_smoke_csv:sha256_shape | artifact_digest.failure_smoke_csv.sha256 | 64 lowercase hex | 64 lowercase hex | pass | Recorded SHA-256 must be a stable 64-character lowercase hex digest. |
| artifact:failure_smoke_csv:sha256 | artifact_digest.failure_smoke_csv.sha256 | 6493e84d30e86eea781840622cb662b6b695a8531810bc843da54f270906560e | 6493e84d30e86eea781840622cb662b6b695a8531810bc843da54f270906560e | pass | Recorded artifact digest must match the current file. |
| artifact:failure_smoke_html:recorded_exists | artifact_digest.failure_smoke_html.exists | True | True | pass | Artifact must be recorded as present. |
| artifact:failure_smoke_html:current_exists | artifact_digest.failure_smoke_html.path | True | True | pass | Recorded artifact path must still exist. |
| artifact:failure_smoke_html:size | artifact_digest.failure_smoke_html.size_bytes | 2808 | 2808 | pass | Recorded artifact size must match the current file. |
| artifact:failure_smoke_html:sha256_shape | artifact_digest.failure_smoke_html.sha256 | 64 lowercase hex | 64 lowercase hex | pass | Recorded SHA-256 must be a stable 64-character lowercase hex digest. |
| artifact:failure_smoke_html:sha256 | artifact_digest.failure_smoke_html.sha256 | e44014a8417c123cf4c157764bab9b4e863af8ff66e4b793e52ddb439872eb26 | e44014a8417c123cf4c157764bab9b4e863af8ff66e4b793e52ddb439872eb26 | pass | Recorded artifact digest must match the current file. |

## Artifacts

| Name | Status | Size | SHA-256 | Path |
| --- | --- | ---: | --- | --- |
| contract_summary_json | pass | 25354 | 73db95c749effdc39d98b4d41c4dcb583c61d9585f786e7e810a503775128a3f | d\460\解释\receipt-failure-smoke-wrapper\receipt-contract-summary\promoted_training_scale_seed_handoff_receipt_contract_summary.json |
| failure_smoke_json | pass | 6738 | 162e95e66de9c048110ad244e1ae1fc18148ef33a5d5d40b54742d9c57fafa4e | d\460\解释\receipt-failure-smoke-wrapper\receipt-contract-failure-smoke\promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.json |
| failure_smoke_csv | pass | 983 | 6493e84d30e86eea781840622cb662b6b695a8531810bc843da54f270906560e | d\460\解释\receipt-failure-smoke-wrapper\receipt-contract-failure-smoke\promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.csv |
| failure_smoke_html | pass | 2808 | e44014a8417c123cf4c157764bab9b4e863af8ff66e4b793e52ddb439872eb26 | d\460\解释\receipt-failure-smoke-wrapper\receipt-contract-failure-smoke\promoted_training_scale_seed_handoff_receipt_contract_check_failure_smoke.html |

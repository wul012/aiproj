# MiniGPT Generation Profile Contract Check

- Status: `pass`
- Decision: `generation_profile_contract_ready`
- Failed count: `0`
- Endpoint profile ids: `['default', 'suppress_newline_tokens']`
- Health profile ids: `['default', 'suppress_newline_tokens']`
- API generation profile: `suppress_newline_tokens`
- API blocked token count: `1`

## Checks

| Check | Category | Status | Target |
| --- | --- | --- | --- |
| profiles_readable | source | pass | e\530\解释\generation-profiles-endpoint\generation-profiles.json |
| health_readable | source | pass | e\530\解释\generation-profiles-endpoint\health-with-generation-profiles.json |
| api_response_readable | source | pass | e\529\解释\generation-profile-playground\api-generate-suppress-newline.json |
| playground_html_readable | source | pass | e\531\解释\generation-profile-current-playground\playground.html |
| default_output_readable | source | pass | e\529\解释\generation-profile-playground\default-omega.txt |
| profile_output_readable | source | pass | e\529\解释\generation-profile-playground\suppress-newline-omega.txt |
| profiles_status_ok | endpoint | pass | profiles.status |
| profiles_default_id | endpoint | pass | profiles.default_generation_profile_id |
| profiles_expected_ids | endpoint | pass | profiles[].id |
| profiles_count_matches | endpoint | pass | profiles.profile_count |
| suppression_profile_blocks_newline | endpoint | pass | blocked_token_texts |
| suppression_profile_blocks_carriage_return | endpoint | pass | blocked_token_texts |
| health_profiles_endpoint | health | pass | health.generation_profiles_endpoint |
| health_profile_ids_match_endpoint | health | pass | health.generation_profiles[].id |
| api_generation_profile | api | pass | api.generation_profile |
| api_blocks_newline | api | pass | blocked_token_texts |
| api_blocks_carriage_return | api | pass | blocked_token_texts |
| api_blocked_token_count_positive | api | pass | api.blocked_token_count |
| api_generated_contains_loss | api | pass | api.generated |
| api_continuation_has_no_newline | api | pass | api.continuation |
| playground_has_profile_select | playground | pass | playground_html |
| playground_fetches_profile_endpoint | playground | pass | playground_html |
| playground_has_profile_loader | playground | pass | playground_html |
| playground_has_cli_profile_flag | playground | pass | playground_html |
| cli_outputs_differ | cli | pass | default_output vs profile_output |
| cli_default_has_newline_split | cli | pass | default_output |
| cli_profile_has_no_newline | cli | pass | profile_output |
| cli_profile_contains_loss | cli | pass | profile_output |

## Issues

- none

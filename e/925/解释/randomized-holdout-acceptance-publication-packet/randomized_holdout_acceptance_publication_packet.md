# MiniGPT randomized holdout acceptance publication packet

- Status: `pass`
- Decision: `randomized_holdout_acceptance_publication_packet_ready`
- Packet ready: `True`
- Handoff: `ready_for_bounded_acceptance_publication_review`
- Accepted claims: `1`
- Blocked claims: `3`
- Promotion: `False`
- Allowed use: `bounded_model_capability_governance_only`

## Evidence

| Kind | Exists | Path |
| --- | --- | --- |
| acceptance_summary | True | e\923\解释\randomized-holdout-acceptance-summary\randomized_holdout_acceptance_summary.json |
| acceptance_summary_contract_check | True | e\924\解释\randomized-holdout-acceptance-summary-check\randomized_holdout_acceptance_summary_check.json |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| acceptance_summary_passed | pass | pass | acceptance summary must pass |
| acceptance_summary_ready | pass | True | acceptance summary must be ready |
| contract_check_passed | pass | pass | contract check must pass |
| contract_check_ready | pass | True | contract check must be ready |
| contract_rebuild_matches | pass | {'original': 'randomized_holdout_acceptance_summary_ready', 'rebuilt': 'randomized_holdout_acceptance_summary_ready'} | contract check must rebuild the acceptance summary decision |
| bounded_acceptance_true | pass | True | publication packet requires bounded acceptance |
| accepted_claim_present | pass | 1 | publication packet needs at least one accepted claim |
| blocked_claims_present | pass | 3 | publication packet must carry blocked claim boundaries |
| allowed_use_bounded | pass | bounded_model_capability_governance_only | allowed use must stay bounded governance only |
| promotion_still_false | pass | False | publication packet must not become direct promotion |
| approved_for_promotion_false | pass | False | direct promotion approval must remain false |
| evidence_files_exist | pass | [{'kind': 'acceptance_summary', 'path': 'e\\923\\解释\\randomized-holdout-acceptance-summary\\randomized_holdout_acceptance_summary.json', 'exists': True}, {'kind': 'acceptance_summary_contract_check', 'path': 'e\\924\\解释\\randomized-holdout-acceptance-summary-check\\randomized_holdout_acceptance_summary_check.json', 'exists': True}] | publication evidence files must exist |

# MiniGPT randomized holdout acceptance publication packet review

- Status: `pass`
- Decision: `randomized_holdout_acceptance_publication_packet_review_ready`
- Review ready: `True`
- Review decision: `accept_publication_packet_for_bounded_downstream_review`
- Bounded publication: `True`
- Promotion: `False`
- Allowed use: `bounded_model_capability_governance_only`
- Scope: `bounded_randomized_holdout_publication_review_only`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| publication_packet_passed | pass | pass | publication packet must pass |
| publication_packet_ready_decision | pass | randomized_holdout_acceptance_publication_packet_ready | publication packet decision must be ready |
| packet_ready | pass | {'packet': True, 'summary': True} | packet and summary must both be ready |
| handoff_ready_for_review | pass | ready_for_bounded_acceptance_publication_review | packet must route to bounded publication review |
| accepted_claim_count | pass | {'summary': 1, 'claims': 1} | review expects exactly one bounded accepted claim |
| blocked_claim_count | pass | {'summary': 3, 'claims': 3} | review expects blocked claim boundaries |
| allowed_use_bounded | pass | {'summary': 'bounded_model_capability_governance_only', 'packet': 'bounded_model_capability_governance_only'} | allowed use must stay bounded governance only |
| promotion_still_false | pass | {'summary': False, 'packet': False} | review must keep direct promotion blocked |
| approved_for_promotion_false | pass | {'summary': False, 'packet': False} | direct promotion approval must remain false |
| contract_check_ready | pass | True | packet must include a passing contract check |
| evidence_count | pass | {'summary': 2, 'rows': 2} | review requires summary and contract-check evidence |
| evidence_files_exist | pass | [{'kind': 'acceptance_summary', 'path': 'e\\923\\解释\\randomized-holdout-acceptance-summary\\randomized_holdout_acceptance_summary.json', 'exists': True}, {'kind': 'acceptance_summary_contract_check', 'path': 'e\\924\\解释\\randomized-holdout-acceptance-summary-check\\randomized_holdout_acceptance_summary_check.json', 'exists': True}] | all publication packet evidence rows must exist |
| packet_checks_clean | pass | 0 | publication packet checks must be clean |

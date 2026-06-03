# MiniGPT model capability route promotion bounded real replay review

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_review_needs_repair`
- Review ready: `True`
- Promotion ready: `False`
- Repair review ready: `True`
- Passed cases: `2/5`
- Diagnosis counts: `{'case_passed': 2, 'no_required_terms_generated_with_unknown_token_surface': 1, 'partial_required_terms_generated_with_unknown_token_surface': 2}`

## Case Reviews

| Case | Pass | Diagnosis | Hit terms | Missed terms | Action |
| --- | --- | --- | --- | --- | --- |
| objective-answer-direct | False | partial_required_terms_generated_with_unknown_token_surface | loss | fixed | target_missing_terms_without_forgetting_hits |
| objective-answer-role | False | no_required_terms_generated_with_unknown_token_surface |  | fixed,loss | repair_prompt_to_required_term_bridge |
| objective-answer-contrast | True | case_passed | fixed,loss |  | keep_case_as_replay_anchor |
| objective-answer-jsonish | True | case_passed | fixed,loss |  | keep_case_as_replay_anchor |
| objective-answer-check | False | partial_required_terms_generated_with_unknown_token_surface | loss | fixed | target_missing_terms_without_forgetting_hits |

# MiniGPT model capability route promotion bounded real replay repair plan

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_repair_plan_ready`
- Ready: `True`
- Task count: `3`
- Source pass rate: `0.4`
- Target pass rate: `1.0`
- Next artifact: `model_capability_route_promotion_bounded_real_replay_repair_seed`

## Repair Tasks

| Task | Case | Type | Missed terms | Surface probe | Focus |
| --- | --- | --- | --- | --- | --- |
| repair-objective-answer-direct | objective-answer-direct | missing_term_retention_repair | fixed | unknown_token_surface_probe | preserve observed hit terms while adding missed required terms |
| repair-objective-answer-role | objective-answer-role | prompt_to_required_terms_bridge_repair | fixed,loss | unknown_token_surface_probe | teach the prompt surface to emit both required terms directly |
| repair-objective-answer-check | objective-answer-check | missing_term_retention_repair | fixed | unknown_token_surface_probe | preserve observed hit terms while adding missed required terms |

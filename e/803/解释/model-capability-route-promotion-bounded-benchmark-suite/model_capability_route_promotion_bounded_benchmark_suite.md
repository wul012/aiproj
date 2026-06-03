# MiniGPT model capability route promotion bounded benchmark suite

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_benchmark_suite_ready`
- Ready: `True`
- Route: `objective_level_contrast`
- Cases: `5`
- Expected terms: `fixed, loss`

## Cases

| Case | Prompt | Expected terms |
| --- | --- | --- |
| objective-answer-direct | 任务：只输出两个英文关键词，表示本轮目标答案。 答案： | fixed,loss |
| objective-answer-role | 目标：给出 paired required terms 的两个角色词。 输出： | fixed,loss |
| objective-answer-contrast | 对比任务：不要解释，只返回目标 pair tokens。 结果： | fixed,loss |
| objective-answer-jsonish | 请用 JSON 风格写出 answer_terms，包含两个英文词。 answer_terms: | fixed,loss |
| objective-answer-check | 自检：本题需要同时出现 fixed 与 loss。最终答案： | fixed,loss |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| consumer_plan_passed | pass | pass | consumer plan must pass |
| consumer_plan_ready | pass | model_capability_route_promotion_consumer_plan_ready | consumer plan decision must be ready |
| route_objective_level_contrast | pass | objective_level_contrast | suite supports objective_level_contrast route |
| bounded_scope | pass | bounded_model_capability_governance_only | suite must stay bounded |
| next_artifact_matches | pass | model_capability_route_promotion_bounded_benchmark_suite | consumer plan must request this suite |
| plan_steps_present | pass | 5 | consumer plan should include enough execution steps |
| non_goals_present | pass | 3 | consumer plan must carry non-goals |

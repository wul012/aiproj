# v834：bounded rebalanced intervention decision

## 本版目标和边界

v834 的目标是收口 v829-v833 的 rebalanced decoder-rescue 分支。v833 已经真实跑过 5 个 decoder profile，结果仍然 `0/5`，并且 `best_any_hit_case_count=0`。继续调采样或直接加训练轮数，已经没有证据支持。

这版不训练新 checkpoint，不修改 benchmark，不修改 expected terms，也不做新 seed。它只做工程路线决策：当前 rescue 分支是否停止，下一步是 objective intervention 还是 architecture/capacity probe。

## 前置链路

- v829：rebalanced seed 修复了 direct/carry 分布。
- v830：用 rebalanced corpus 训练出真实 checkpoint。
- v831：四方比较显示 rebalanced checkpoint 仍是 `0/5`，低于 v806 baseline。
- v832：失败诊断确认分布已修但 replay zero-hit、fragment-like。
- v833：5 个 decoder profile sweep 均无恢复，best profile 仍无 required-term hit。

v834 接住 v833 的 `route_to_objective_or_architecture_intervention`。

## 关键文件

`src/minigpt/model_capability_route_promotion_bounded_rebalanced_intervention_decision.py`

核心 builder。它读取 v829-v833 的五份证据，抽取 `signals`，生成 `evidence_rows`，再给出 `route` 和 `summary`。

关键字段：

- `signals`：把分布修复、训练完成、比较失败、zero-hit、profile sweep 无恢复等事实压成可判断字段。
- `evidence_rows`：按 stage 记录关键证据，便于 CSV、Markdown、HTML 和后续版本读取。
- `route`：保存关闭的分支、证据窗口、选中的干预 track、fallback track、禁止动作和 stop reasons。
- `summary`：README/CLI 消费的扁平摘要，明确 `promotion_allowed=False`、`new_training_allowed=False`。
- `interpretation`：明确 `model_quality_claim=route_decision_only`。

`src/minigpt/model_capability_route_promotion_bounded_rebalanced_intervention_decision_artifacts.py`

产物层。输出 JSON、CSV、text、Markdown 和 HTML。CSV 保存 evidence rows，HTML 展示路线决策、证据、stop reasons 和 blocked actions。

`scripts/build_model_capability_route_promotion_bounded_rebalanced_intervention_decision.py`

CLI 入口。显式接收 v829 seed、v830 training、v831 comparison、v832 diagnostic、v833 profile sweep，避免隐藏路径推断。

`tests/test_model_capability_route_promotion_bounded_rebalanced_intervention_decision.py`

测试覆盖停止 rescue、部分 profile 恢复时转入 review、分布未修时不允许关闭分支、CLI/locator/artifact 输出。

## 核心决策逻辑

builder 不只看 v833，而是按顺序确认：

- rebalanced seed 分布已经修复：`direct_answer_share >= 0.2` 且 `carry_forward_share <= 0.5`。
- rebalanced training run 已完成并有 loss 记录。
- checkpoint comparison 没有 promotion-ready，也没有恢复到 baseline。
- failure diagnostic 显示所有 case zero-hit。
- profile sweep 显示所有 decoder profile 都没有恢复。

只有这些条件都成立，才输出：

`stop_rebalanced_decoder_rescue_and_design_objective_contract_intervention`

这避免了过早关闭分支：如果 profile sweep 有部分恢复，decision 会转成 partial recovery review；如果 profile sweep promotable，也不会直接进入 intervention。

## 真实运行命令

```powershell
python scripts\build_model_capability_route_promotion_bounded_rebalanced_intervention_decision.py `
  --rebalanced-seed e\829\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-seed-revision `
  --training-run e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run `
  --comparison e\831\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-checkpoint-comparison `
  --failure-diagnostic e\832\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-failure-diagnostic `
  --profile-sweep e\833\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-profile-sweep `
  --out-dir e\834\解释\model-capability-route-promotion-bounded-rebalanced-intervention-decision `
  --require-decision-ready `
  --require-intervention-selected `
  --force
```

## 真实结果

- `status=pass`
- `decision=stop_rebalanced_decoder_rescue_and_design_objective_contract_intervention`
- `selected_intervention_track=objective_contract_intervention_first`
- `fallback_intervention_track=architecture_capacity_probe_if_objective_contract_fails`
- `recommended_next_artifact=model_capability_route_promotion_bounded_objective_intervention_plan`
- `promotion_allowed=False`
- `new_training_allowed=False`
- `profile_sweep_no_recovery=True`
- `best_any_hit_case_count=0`
- `model_quality_claim=route_decision_only`

## 测试覆盖

focused tests：

- v833 无恢复时，关闭 rebalanced decoder rescue 并选择 objective-contract intervention。
- profile sweep 有部分恢复时，进入 partial recovery review，而不是直接干预。
- 分布未修时，不允许关闭分支。
- CLI、locator、JSON/CSV/text/Markdown/HTML 输出全部连通。

## 运行证据

- 决策报告：`e/834/解释/model-capability-route-promotion-bounded-rebalanced-intervention-decision/`
- 截图：`e/834/图片/v834-bounded-rebalanced-intervention-decision-html.png`

## 一句话总结

v834 把 rebalanced decoder-rescue 从“继续试试”变成“证据充分，关闭分支，转入 objective-contract intervention”。

# v594 required-term pair loss-branch route decision

## 本版目标和边界

v594 接 v593 的 comparison 结论：三条 loss-branch objective 全部是 `loss-only tradeoff`。本版新增 route decision，判断这些 route 是否能推广、是否应该继续训练、下一步该选哪条做稳定性基线。

本版不训练、不新增 corpus、不做模型质量宣称。它是 route selection 层。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_branch_route_decision.py
src/minigpt/model_capability_required_term_pair_loss_branch_route_decision_artifacts.py
scripts/run_model_capability_required_term_pair_loss_branch_route_decision.py
tests/test_model_capability_required_term_pair_loss_branch_route_decision.py
e/594/解释/model-capability-required-term-pair-loss-branch-route-decision/
```

## 输入输出

输入：

```text
e/593/解释/model-capability-required-term-pair-loss-branch-objective-comparison/model_capability_required_term_pair_loss_branch_objective_comparison.json
```

输出：

```text
model_capability_required_term_pair_loss_branch_route_decision.json
model_capability_required_term_pair_loss_branch_route_decision.csv
model_capability_required_term_pair_loss_branch_route_decision.md
model_capability_required_term_pair_loss_branch_route_decision.html
```

## 核心字段

`route_rows` 为每条路线生成：

```text
route_type
hit_terms
missed_terms
pair_full_observed
loss_only_tradeoff
complexity_score
stability_replay_candidate
rejection_reasons
```

`summary` 负责给出路线级判断：

```text
pair_full_route_count=0
loss_only_tradeoff_route_count=3
selected_stability_route=v590-targeted
fixed_retention_objective_required=True
```

选择 targeted 的原因不是它更好，而是它是最简单的 loss-only route，适合作为 v595 稳定性基线。

## 测试覆盖

测试覆盖：

- loss-only 三路线会选择 targeted 作为稳定性基线。
- 如果有 pair-full route，则走 promotion decision。
- comparison 失败时 decision 失败。
- CLI 在 `--require-pass` 下对坏输入返回非零。
- 五种输出格式都可生成。

## 运行结论

```text
decision=select_targeted_loss_branch_for_seed_stability_not_promotion
fixed_retention_objective_required=True
```

## 一句话总结

v594 把 loss-only tradeoff 从比较结果转成执行策略：不推广，只用 targeted 做稳定性基线，然后转向 fixed-retention objective。

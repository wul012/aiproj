# v587 required-term pair objective closeout

## 本版目标和边界

v587 是 v579-v586 的收口版。它不再训练、不再加 corpus，而是把两条机器决策合并：

```text
v583 branch-binding route decision
v586 target-anchor route decision
```

目标是给下一版提供明确路线：当前 objective 已经关闭，下一步必须做 loss-branch objective。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_objective_closeout.py
src/minigpt/model_capability_required_term_pair_objective_closeout_artifacts.py
scripts/run_model_capability_required_term_pair_objective_closeout.py
tests/test_model_capability_required_term_pair_objective_closeout.py
```

## 核心字段

summary 中关键字段：

```text
branch_binding_stopped
target_anchor_residual_only
residual_signal_routes
loss_branch_required
```

真实结果：

```text
branch_binding_stopped=True
target_anchor_residual_only=True
loss_branch_required=True
```

## 决策逻辑

如果 branch-binding 没有停止，或 target-anchor 不是 residual-only，closeout 会 fail。

当前输入都通过，因此 decision 是：

```text
close_current_objectives_and_design_loss_branch_objective
```

## 测试覆盖

测试覆盖：

- 正常 closeout 会要求 loss-branch objective。
- branch-binding 未停止时 closeout fail。
- JSON/CSV/text/Markdown/HTML 输出完整。
- 输入目录能自动定位对应 JSON。

## 链路角色

v587 是路线闸门。它避免继续在已知负收益 objective 上消耗训练版本，同时保留 v571/v584 的 residual fixed signal。

## 一句话总结

v587 正式关闭当前 branch-binding/target-anchor objective，下一步必须转向 loss branch objective。

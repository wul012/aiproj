# v583 required-term pair branch-binding route decision

## 本版目标和边界

v583 把 v582 的人工可读 comparison 转成机器可读 route decision。它解决的问题是：branch-binding v1/v2 已经连续负结果，后续不能靠记忆来避免重复推进。

本版不训练、不改 corpus、不提升模型能力。它只生成停止条件。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_branch_binding_route_decision.py
src/minigpt/model_capability_required_term_pair_branch_binding_route_decision_artifacts.py
scripts/run_model_capability_required_term_pair_branch_binding_route_decision.py
tests/test_model_capability_required_term_pair_branch_binding_route_decision.py
```

主模块读取 v582 comparison，按 source label 和 corpus mode 判断 route type。包含 `branch-binding` 或 `branch_binding` 的路线会被归类为 `branch_binding`，其余为 baseline。

## 核心字段

summary 里最重要的字段：

```text
branch_binding_route_count
branch_binding_pair_full_route_count
branch_binding_visible_hit_route_count
baseline_visible_hit_route_count
best_residual_signal
stop_branch_binding_v1
branch_binding_regressed_below_baseline
```

v583 的真实结果是：

```text
branch_binding_route_count=2
branch_binding_visible_hit_route_count=0
best_residual_signal=v571-loss-balanced
```

这说明 v579/v581 没有 visible hit，而 v571 至少保留了 fixed partial hit。

## 决策逻辑

如果 branch-binding 路线出现 pair-full，decision 会进入 promotion：

```text
promote_branch_binding_pair_full_route
```

v583 的输入没有 pair-full，而且 branch-binding visible hit 低于 baseline，因此结果是：

```text
stop_branch_binding_v1_and_keep_residual_baseline
```

## 测试覆盖

测试覆盖四类行为：

- v571/v579/v581 fixture 产生停止 branch-binding 的决策。
- branch-binding 如果出现 pair-full 会切换为 promotion。
- 输入失败时 `--require-pass` 返回失败。
- JSON/CSV/text/Markdown/HTML 输出都能生成。

## 链路角色

v583 是 branch-binding route 的闸门。它让后续版本必须拿出更强 objective 才能继续训练，否则应停止 v579/v581 同类变体。

## 一句话总结

v583 把 branch-binding v1/v2 的负结果沉淀为机器可读停止决策，保留 v571 作为 residual baseline，但不宣称模型质量提升。

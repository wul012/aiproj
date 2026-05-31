# v586 required-term pair target-anchor route decision

## 本版目标和边界

v586 把 v585 的 comparison 结果变成 route decision。它解决的问题是：v584 target-anchor 有 partial fixed hit，但不能因为“比 v579/v581 好”就被误推广。

本版不训练、不改语料、不宣称模型能力提升。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_target_anchor_route_decision.py
src/minigpt/model_capability_required_term_pair_target_anchor_route_decision_artifacts.py
scripts/run_model_capability_required_term_pair_target_anchor_route_decision.py
tests/test_model_capability_required_term_pair_target_anchor_route_decision.py
```

主模块从 comparison 中识别三类 route：

- `target_anchor`
- `branch_binding`
- `baseline`

然后判断 target-anchor 是否 pair-full、是否命中 loss、是否只是 residual fixed-only。

## 核心字段

summary 关键字段：

```text
target_anchor_route_count
target_anchor_pair_full_route_count
target_anchor_visible_hit_route_count
target_anchor_loss_hit_route_count
residual_signal_routes
target_anchor_residual_only
```

v586 实际结果：

```text
target_anchor_route_count=1
target_anchor_visible_hit_route_count=1
target_anchor_loss_hit_route_count=0
residual_signal_routes=v571-loss-balanced,v584-target-anchor
```

## 决策逻辑

如果 target-anchor 有 pair-full：

```text
promote_target_anchor_pair_full_route
```

当前只有 fixed partial hit，因此决策是：

```text
keep_target_anchor_as_residual_not_promoted
```

## 测试覆盖

测试覆盖：

- v585 fixture 产生 residual-not-promoted 决策。
- target-anchor 出现 pair-full 时切换 promotion。
- 输入失败时 `--require-pass` 退出码为 1。
- JSON/CSV/text/Markdown/HTML 输出都能生成。

## 链路角色

v586 是 target-anchor route 的闸门。它保留 v584 作为证据，但阻止其被误当作成功路线。

## 一句话总结

v586 明确 target-anchor 只是 residual evidence，下一步必须设计 loss-branch objective 才能继续推进模型能力。

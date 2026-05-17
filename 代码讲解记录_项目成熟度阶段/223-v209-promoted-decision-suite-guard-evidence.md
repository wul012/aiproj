# v209 promoted decision suite guard evidence 代码讲解

## 本版目标

v209 的目标是把 v208 已经进入 promoted training-scale comparison 的 handoff suite guard evidence，继续带到 promoted baseline decision。

v208 让 promoted comparison 的每个 promoted input 都保留了 `handoff_require_suite_consistency`、`handoff_suite_consistency`、`handoff_suite_mismatch_count` 和 `handoff_selected_suite_path`。但真正会进入下一轮训练规划的是 baseline decision，如果 decision 只记录 selected run 的真实 `suite_path`，却不记录它继承的 handoff suite guard，后续 seed 和人工复核仍然需要回翻 comparison。

本版补上这一步，让 promoted baseline decision 同时保留：

1. 真实 comparison 计算出来的 selected suite path。
2. 上游 handoff guard 传下来的 selected handoff suite evidence。

## 不做什么

本版不重新计算 suite consistency，不改变 `--require-suite-consistency` 的阻断条件，不改变 candidate/rejected 判定，不改变 readiness score 和 baseline selection 排序。

`suite_consistency` 仍然来自 promoted comparison summary。v209 只把 comparison row 与 summary 里的 handoff suite guard 透传到 decision row、selected baseline、summary、artifact 和 CLI 输出。

## 前置路线

v202-v208 已经形成了：

```text
training-scale comparison -> decision -> workflow -> handoff -> promotion -> promotion index -> promoted comparison
```

v209 再往下游推进一层：

```text
promoted comparison -> promoted baseline decision
```

这一步的价值在于 baseline decision 是下一轮 promoted seed 的直接上游。它应该同时说明“为什么这个 run 被选中”和“这个 run 带着哪条 handoff suite boundary 被选中”。

## `src/minigpt/promoted_training_scale_decision.py`

### `_promotion_rows()`

decision 读取 promoted comparison 的 `promotions`。v209 为每个 promotion row 增加四个字段：

```python
"handoff_require_suite_consistency"
"handoff_suite_consistency"
"handoff_suite_mismatch_count"
"handoff_selected_suite_path"
```

这些字段来自 comparison，不来自 scale run。这样 selected baseline 被复制出来时，也能保留上游 handoff guard。

### `_summary()`

summary 新增 selected-level 和 aggregate-level 两类字段。

selected-level 字段：

```python
selected_handoff_require_suite_consistency
selected_handoff_suite_consistency
selected_handoff_suite_mismatch_count
selected_handoff_selected_suite_path
```

这些字段回答“被选中的 baseline 自己继承的 handoff suite boundary 是什么”。

aggregate-level 字段：

```python
handoff_require_suite_consistency_count
handoff_suite_consistent_count
handoff_suite_mismatch_total
comparison_ready_handoff_suite_mismatch_total
```

这些字段优先消费 comparison summary；如果旧 comparison 没有这些字段，就从 decision promotions 里轻量补算，保证兼容旧产物。

### CSV/Markdown/HTML

CSV 新增 selected handoff 和 aggregate handoff 字段，方便机器消费。

Markdown summary 新增：

```text
Selected handoff suite
Selected handoff mismatches
Selected handoff suite path
Handoff suite consistent
Handoff suite mismatches
```

HTML stats 同步展示这些字段，让人工审阅 baseline decision 时无需再打开 comparison JSON。

## `scripts/decide_promoted_training_scale_baseline.py`

CLI stdout 新增：

```text
selected_handoff_suite_consistency
selected_handoff_suite_mismatch_count
handoff_suite_consistent_count
handoff_suite_mismatch_total
```

这样 smoke 和 CI 可以直接确认 decision 读到了 promoted comparison 的 handoff guard。

## 测试覆盖

`tests/test_promoted_training_scale_decision.py` 新增 `test_carries_promoted_comparison_handoff_suite_guard_into_decision_outputs_and_script`。

这个测试构造带 handoff suite guard 的 promotion index，通过 promoted comparison 生成 comparison report，再交给 promoted decision 选择 baseline。它覆盖：

1. selected baseline row 保留 handoff suite guard。
2. decision summary 记录 selected handoff suite status、mismatch count 和 selected suite path。
3. CSV/Markdown/HTML 输出包含这些字段。
4. CLI stdout 打印 selected handoff suite 和 handoff mismatch 总数。

原有测试继续覆盖 accepted baseline、insufficient promoted inputs、blocked comparison、HTML escaping、mixed-suite strict guard，确保 v209 不改变 baseline decision 语义。

## 运行证据

本版运行证据归档在 `c/209`：

- `图片/01-promoted-training-scale-decision-tests.png`
- `图片/02-promoted-training-scale-decision-smoke.png`
- `图片/03-promoted-decision-artifact-suite-guard-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些证据分别证明：聚焦测试通过、CLI decision 能跑通、四类 artifact 都带 selected handoff 字段、source encoding 仍干净、全量 unittest 通过、README 和归档说明已经对齐。

## 证据链角色

v209 处在 promoted comparison 和 promoted seed 之间。它让 baseline decision 成为更完整的 handoff packet：既包含真实 comparison 选出的 baseline，也包含该 baseline 继承来的 handoff suite guard context。

## 一句话总结

v209 把 promoted-comparison handoff suite guard 接到 promoted baseline decision，让下一轮 seed 的上游决策继续保留 clean-comparison 边界。

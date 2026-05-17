# v210 promoted seed suite guard evidence 代码讲解

## 本版目标

v210 的目标是把 v209 已经进入 promoted baseline decision 的 handoff suite guard evidence，继续带到 promoted training-scale seed。

v209 让 baseline decision 能记录 selected baseline 的 `selected_handoff_suite_consistency`、`selected_handoff_suite_mismatch_count` 和 `selected_handoff_selected_suite_path`。但 promoted seed 是下一轮 `plan_training_scale.py` 的直接上游，如果 seed 只继承真实 `suite_path`，却不保存 decision 的 handoff guard，下一轮训练规划入口仍然缺少上游 clean-comparison 边界。

本版补上这一步，让 seed 同时保留：

1. 从 selected scale run 继承来的真实 suite path，用于生成下一轮 plan command。
2. 从 promoted decision 传下来的 handoff suite guard，用于解释这个 baseline 的上游 suite 边界。

## 不做什么

本版不重新计算 suite consistency，不改变 seed blocker，不改变 next plan command 的生成逻辑，也不改变 `--suite-name` / `--suite` 的选择规则。

下一轮命令继续由 `next_plan["suite"]` 决定；handoff guard 只进入 `baseline_seed["handoff_suite_guard"]` 和 summary/artifact/CLI 输出。

## 前置路线

v202-v209 已经形成：

```text
training-scale comparison -> decision -> workflow -> handoff -> promotion -> promotion index -> promoted comparison -> promoted decision
```

v210 再推进一层：

```text
promoted decision -> promoted seed
```

这一步很关键，因为 seed 是下一轮训练规模规划的入口。它既要能生成命令，也要能解释这条命令继承自哪个 baseline 和哪条 handoff suite boundary。

## `src/minigpt/promoted_training_scale_seed.py`

### `baseline_seed["handoff_suite_guard"]`

`build_promoted_training_scale_seed()` 现在会调用 `_handoff_suite_guard(decision, selected)`，并把结果写入 `baseline_seed`：

```python
"handoff_suite_guard": {
    "selected_handoff_require_suite_consistency": ...,
    "selected_handoff_suite_consistency": ...,
    "selected_handoff_suite_mismatch_count": ...,
    "selected_handoff_selected_suite_path": ...,
    "handoff_suite_consistent_count": ...,
    "handoff_suite_mismatch_total": ...,
}
```

这些字段优先来自 decision summary；如果 summary 没有，则 selected baseline row 的旧字段可以兜底。这样 seed 能兼容 v209 之后的新 decision，也不会拒绝较旧的 decision 产物。

### `_summary()`

seed summary 新增：

```python
selected_handoff_require_suite_consistency
selected_handoff_suite_consistency
selected_handoff_suite_mismatch_count
selected_handoff_selected_suite_path
handoff_suite_consistent_count
handoff_suite_mismatch_total
```

这些字段回答“本轮 seed 继承的 baseline 带着什么 handoff suite boundary 进入下一轮规划”。

## `src/minigpt/promoted_training_scale_seed_artifacts.py`

CSV 新增 selected handoff 与 handoff total 字段，便于机器消费。

Markdown summary 新增：

```text
Selected handoff suite
Selected handoff mismatches
Selected handoff suite path
Handoff suite consistent
Handoff suite mismatches
```

HTML stats 与 Baseline Seed 表同步展示这些字段，方便人工复核 seed 时不用回翻 decision JSON。

## `scripts/build_promoted_training_scale_seed.py`

CLI stdout 新增：

```text
selected_handoff_suite_consistency
selected_handoff_suite_mismatch_count
handoff_suite_mismatch_total
```

这样 smoke 和 CI 可以直接确认 seed 消费到了 decision handoff guard。

## 测试覆盖

`tests/test_promoted_training_scale_seed.py` 新增 `test_carries_decision_handoff_suite_guard_into_seed_outputs_and_script`。

这个测试构造带 handoff suite guard 的 decision，再构建 ready seed，覆盖：

1. `baseline_seed["handoff_suite_guard"]` 保留 selected handoff suite 字段。
2. seed summary 输出 selected handoff suite status、mismatch count 和 selected suite path。
3. CSV/Markdown/HTML 输出包含这些字段。
4. CLI stdout 打印 selected handoff suite 和 handoff mismatch 总数。
5. next plan command 仍然生成，不被 handoff guard 改变。

原有测试继续保护 accepted/review/blocked seed、missing source blocker、standard suite inheritance、default suite override、HTML escaping 和 artifact facade 导出。

## 运行证据

本版运行证据归档在 `c/210`：

- `图片/01-promoted-training-scale-seed-tests.png`
- `图片/02-promoted-training-scale-seed-smoke.png`
- `图片/03-promoted-seed-artifact-suite-guard-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些证据分别证明：聚焦测试通过、CLI seed 能跑通、四类 artifact 都带 selected handoff 字段、source encoding 仍干净、全量 unittest 通过、README 和归档说明已经对齐。

## 证据链角色

v210 处在 promoted decision 和 promoted seed handoff 之间。它让下一轮训练规划入口既可执行，又可解释 selected baseline 的 clean-comparison 边界。

## 一句话总结

v210 把 promoted baseline decision 的 handoff suite guard 接到 next-cycle seed，让下一轮训练规模规划入口继续保留 clean-comparison 边界。

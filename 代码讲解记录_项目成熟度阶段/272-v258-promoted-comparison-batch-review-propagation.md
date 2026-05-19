# v258 promoted comparison batch review propagation

## 本版目标和边界

v258 的目标是把 v257 promotion index 中保留下来的 handoff selected batch review/blocker context 继续传到 promoted training scale comparison。promoted comparison 是真正调用 training-scale run comparison 的 promoted-only 视图，如果这里只保留 run score/gate/batch/suite，就会把“这些 compare-ready promoted inputs 是否仍带 selected batch review/blocker 风险”隐藏掉。

本版不改变 promoted-only comparison 规则：只有 promotion index 里 `promoted_for_comparison=True` 的 run 会进入比较。selected batch review/blocker 仍是风险上下文和 recommendation，不会让比较自动 blocked。

## 前置链路

这版延续 v250-v257：

- v250-v252：portfolio comparison review action 进入 batch summary。
- v253：batch review/blocker counts 进入 gated scale run 和 run comparison。
- v254：run decision 记录 selected-run batch review status。
- v255：controlled handoff 保留 decision batch review context。
- v256：promotion acceptance 保留 handoff batch review context。
- v257：promotion index 在 promoted-only compare 选择前保留这组 context。
- v258：promoted comparison 在真实 promoted-only run comparison 前后继续保留这组 context。

它是下游证据传播，不是新的评分逻辑，也不是新的模型能力提升。

## 关键文件

### `src/minigpt/promoted_training_scale_comparison.py`

`_promotion_rows()` 现在从 promotion index row 中读取 handoff batch review 字段：

- `handoff_selected_batch_review_status`
- `handoff_selected_batch_comparison_review_action_count`
- `handoff_selected_batch_comparison_blocker_action_count`
- `handoff_selected_batch_maturity_coverage_regression_count`
- `handoff_batch_comparison_review_action_count`
- `handoff_batch_comparison_blocker_action_count`
- `handoff_batch_comparison_blocker_reasons`

`_summary()` 新增 comparison-ready 聚合字段：

- `comparison_ready_handoff_selected_batch_review_count`
- `comparison_ready_handoff_selected_batch_blocker_count`
- `comparison_ready_handoff_selected_batch_comparison_review_action_total`
- `comparison_ready_handoff_selected_batch_comparison_blocker_action_total`
- `comparison_ready_handoff_batch_comparison_review_action_total`
- `comparison_ready_handoff_batch_comparison_blocker_action_total`
- `comparison_ready_handoff_batch_comparison_blocker_reasons`

这些字段只统计 `promoted_for_comparison=True` 的 run，避免 review/blocked promotion 的风险被误算进真正比较输入。

`_recommendations()` 在 compared 和 blocked 两种路径中都检查这组字段。存在 blocker 时提示先解决 selected handoff batch blocker actions，存在 review 时提示先复核 selected handoff batch review actions。

### `src/minigpt/promoted_training_scale_comparison_artifacts.py`

CSV 输出新增 handoff batch review 字段。

Markdown 摘要区新增 comparison-ready selected batch review/blocker counts 和 action totals；Promoted Inputs 表新增 `Batch Review`、`Batch Blockers` 列。

HTML stats cards 和 Promoted Inputs 表同步展示这两个风险字段。

### `scripts/compare_promoted_training_scale_runs.py`

CLI 输出新增：

- `comparison_ready_handoff_selected_batch_review_count`
- `comparison_ready_handoff_selected_batch_blocker_count`
- `comparison_ready_handoff_selected_batch_comparison_review_action_total`
- `comparison_ready_handoff_selected_batch_comparison_blocker_action_total`
- `comparison_ready_handoff_batch_comparison_blocker_reasons`

这样 CI 日志能直接确认 promoted comparison 是否带着 batch review/blocker 风险。

### `tests/test_promoted_training_scale_comparison.py`

新增测试 `test_carries_index_handoff_batch_review_context_into_outputs_and_script()`，用两个 promoted inputs 模拟 index 输出：

- `alpha` 带 selected batch blocker。
- `beta` 带 selected batch review。

测试确认：

- promoted-only comparison 仍然 `compared`。
- summary 只聚合 comparison-ready 输入的 batch review/blocker counts。
- CSV、Markdown、HTML、CLI 都暴露新增字段。

## 输入输出

输入是 `training_scale_promotion_index.json` 或 promotion index 目录。

输出仍是：

- `promoted_training_scale_comparison.json`
- `promoted_training_scale_comparison.csv`
- `promoted_training_scale_comparison.md`
- `promoted_training_scale_comparison.html`

这些输出是 promoted-only comparison evidence，不是最终 baseline acceptance。是否选择某个 run 做下一轮 baseline，仍由 promoted baseline decision 层继续判断。

## 测试覆盖

- focused tests 覆盖 promoted comparison、promoted decision、promotion index、promotion 和 handoff 相邻链路。
- 全量 unittest 确认新增字段没有破坏其他治理链路。
- source encoding 检查防止 BOM 或语法错误进入 CI。
- 结构检查确认 source、script、test、README、讲解和 `c/258` 归档都包含关键字段。

## 运行证据

运行截图和解释归档在 `c/258`：

- `c/258/图片/01-focused-tests.png`
- `c/258/图片/02-promoted-comparison-batch-review-smoke.png`
- `c/258/图片/03-promoted-comparison-html.png`
- `c/258/图片/04-full-unittest.png`
- `c/258/图片/05-source-encoding.png`
- `c/258/图片/06-docs-check.png`
- `c/258/解释/说明.md`

## 一句话总结

v258 让 promoted comparison 从“只比较 promoted runs”升级为“比较 promoted runs 时继续保留 comparison-ready selected batch review/blocker 风险”。

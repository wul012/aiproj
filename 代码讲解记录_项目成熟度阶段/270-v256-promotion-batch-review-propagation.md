# v256 promotion batch review propagation

## 本版目标和边界

v256 的目标是把 v255 controlled handoff 中的 selected batch review status 继续传到 training scale promotion。promotion 层负责判断已执行 handoff 是否可以作为项目证据和下一轮 baseline 的候选，因此它需要看到 handoff 背后的 batch comparison review/blocker 语义。

本版不改变 promotion 三态规则：handoff 完成、batch 完成、variant artifact 齐全时仍可 `promoted`。selected batch review/blocker 不被默认升级为 blocker。v256 做的是证据传播和 recommendation 提醒，避免 promotion evidence 把上游风险吞掉。

## 前置链路

这版延续 v250-v255：

- v250-v252：portfolio comparison review action 进入 batch summary。
- v253：batch review summary 进入 scale run 和 run comparison。
- v254：run decision 记录 selected batch review status。
- v255：controlled handoff 保留 selected batch review status。
- v256：training scale promotion 保留 handoff batch review context。

这仍然是下游证据传播，不是横向新增报告。

## 关键文件

### `src/minigpt/training_scale_promotion.py`

`_suite_guard()` 现在从 handoff summary 或 decision summary 中读取：

- `selected_batch_review_status`
- `selected_batch_comparison_review_action_count`
- `selected_batch_comparison_blocker_action_count`
- `selected_batch_maturity_coverage_regression_count`
- `batch_comparison_review_action_count`
- `batch_comparison_blocker_action_count`
- `batch_maturity_coverage_regression_count`
- `batch_comparison_blocker_reasons`

这些字段进入 promotion summary，命名前缀为 `handoff_`，说明它们来自 handoff 层，而不是 promotion 自己重新计算的结果。

`_recommendations()` 在输出 promoted/review/blocker 默认建议前，先检查 handoff selected batch review status：

- `blocker`：提示先解决 selected batch comparison blocker action。
- `review`：提示先复核 selected batch comparison action。

这不会改变 `promotion_status`，但会让 promotion-ready 的语义更诚实。

### `src/minigpt/training_scale_promotion_artifacts.py`

CSV 新增 handoff batch review 字段，Markdown/HTML 摘要区同步显示：

- handoff selected batch review status
- selected review/blocker counts
- handoff batch comparison review/blocker totals

这样人工读 promotion 报告时，不必再回查 handoff JSON 才能发现上游 batch comparison 风险。

### `tests/test_training_scale_promotion.py`

测试 fixture `make_completed_handoff_tree()` 支持 `selected_batch_review_status`。

新增断言覆盖：

- clean 状态保持旧 promoted 语义。
- review 状态进入 promotion summary、CSV、Markdown、HTML。
- blocker 状态进入 promotion summary，并优先输出 blocker recommendation。

## 输入输出

输入是 `training_scale_handoff.json` 以及 handoff 指向的 scale run、batch、variant portfolio artifacts。

输出是：

- `training_scale_promotion.json`
- `training_scale_promotion.csv`
- `training_scale_promotion.md`
- `training_scale_promotion.html`

这些输出是 promotion acceptance 证据，不是模型效果证明。模型是否变强仍取决于真实 checkpoint、固定 suite、scorecard 和 repeated training delta。

## 测试覆盖

- 聚焦测试覆盖 `training_scale_promotion`、`training_scale_handoff`、`training_scale_run_decision`。
- 全量 unittest 确认新增字段没有破坏其他治理链路。
- source encoding 检查防止 BOM 或语法错误进入 CI。

## 运行证据

运行截图和解释归档在 `c/256`：

- `c/256/图片/01-focused-tests.png`
- `c/256/图片/02-structure-check.png`
- `c/256/图片/03-full-unittest.png`
- `c/256/图片/04-source-encoding.png`
- `c/256/解释/说明.md`

## 一句话总结

v256 让 promotion acceptance 从“接收完成的 handoff”升级为“接收 handoff 时继续保留 selected batch review/blocker 风险”。

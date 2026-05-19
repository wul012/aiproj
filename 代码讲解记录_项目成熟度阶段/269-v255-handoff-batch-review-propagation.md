# v255 handoff batch review propagation

## 本版目标和边界

v255 的目标是把 v254 run decision 中的 selected batch review status 继续传到 controlled training scale handoff。handoff 层是 execute command 被人工审阅、验证或执行的入口，因此它应该保留 selected run 背后的 batch comparison review/blocker 语义，而不是只展示 decision status 和命令。

本版不改变 handoff 的执行规则，不新增训练动作，也不自动执行任何命令。`review` 决策是否允许 handoff 仍由 `allow_review` 控制。v255 只增强证据字段和 recommendation 文案，让风险在交接层不丢失。

## 前置链路

这版延续 v250-v254：

- v250-v252：portfolio comparison 的 review action 进入 batch summary。
- v253：batch review summary 进入 gated scale run 和 run comparison。
- v254：run decision 保留 selected batch review status。
- v255：handoff 继续保留 selected batch review status。

它属于下游证据传播，不是新报告扩展。

## 关键文件

### `src/minigpt/training_scale_handoff.py`

`_summary()` 从 decision summary 中读取：

- `selected_batch_review_status`
- `selected_batch_comparison_review_action_count`
- `selected_batch_comparison_blocker_action_count`
- `selected_batch_maturity_coverage_regression_count`
- `batch_comparison_review_action_count`
- `batch_comparison_blocker_action_count`
- `batch_maturity_coverage_regression_count`
- `batch_comparison_blocker_reasons`

这些字段进入 handoff JSON summary，成为后续 promotion 或人工审阅可以消费的证据。

`write_training_scale_handoff_csv()` 增加对应列，保证机器读取时不需要只依赖 JSON。

`render_training_scale_handoff_markdown()` 和 `render_training_scale_handoff_html()` 在摘要区展示 selected batch review status、selected review/blocker 计数和 comparison 级别计数，避免人工只看到命令和 artifact count。

`_recommendations()` 新增两类提示：

- selected batch blocker：先解决 blocker action，再把 handoff 当作 clean evidence。
- selected batch review：先复核 review action，再执行命令。

### `tests/test_training_scale_handoff.py`

测试 fixture 的 fake decision 现在带 v254 的 batch review 字段。

新增/加强断言覆盖：

- planned handoff 能看到 `selected_batch_review_status=review`
- Markdown/HTML 能显示 selected batch review 字段
- blocker 状态会进入 handoff summary，并产生 blocker recommendation

这些测试保护的是 decision -> handoff 的字段传播。

## 输入输出

输入仍是 `training_scale_workflow.json` 以及 workflow 中引用的 `training_scale_run_decision.json`。

输出仍是：

- `training_scale_handoff.json`
- `training_scale_handoff.csv`
- `training_scale_handoff.md`
- `training_scale_handoff.html`

这些输出是 execute handoff 证据，不是模型效果证明。模型是否变好仍需要真实 checkpoint、固定 suite、scorecard 和 repeated training delta 支撑。

## 测试覆盖

- 聚焦测试覆盖 `training_scale_handoff`、`training_scale_run_decision`、`training_scale_run_comparison`、`training_scale_run`。
- 全量 unittest 确认新增字段没有破坏训练治理、发布治理、评估治理和 UI 相关模块。
- source encoding 检查防止 BOM 或语法错误进入 CI。

## 运行证据

运行截图和解释归档在 `c/255`：

- `c/255/图片/01-focused-tests.png`
- `c/255/图片/02-structure-check.png`
- `c/255/图片/03-full-unittest.png`
- `c/255/图片/04-source-encoding.png`
- `c/255/解释/说明.md`

## 一句话总结

v255 让 controlled handoff 从“命令交接”升级为“带着 selected run batch review/blocker 风险一起交接”。

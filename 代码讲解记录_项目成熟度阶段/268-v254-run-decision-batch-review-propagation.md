# v254 run decision batch review propagation

## 本版目标和边界

v254 的目标是把 v253 已经进入 `training_scale_run_comparison` 的 batch comparison review 摘要继续传到 `training_scale_run_decision`。决策层负责选择哪个 gated scale run 可以进入 `--execute`，因此它不能只看到 readiness score、gate status 和 batch status，也应该保留 selected run 背后的 review/blocker 风险。

本版不新增训练能力，不改变 scale gate 的放行语义，也不默认阻止带 review action 的 run。它只在选中 run 带 batch comparison blocker action 时，把原本可能为 `ready` 的决策降为 `review`，让 execute command 前的证据保持审慎。

## 前置链路

这版来自 v250-v253 的连续链路：

- v250：portfolio comparison 开始消费 coverage regression。
- v251：portfolio comparison review action 逻辑拆分。
- v252：batch report 记录 comparison review summary。
- v253：gated scale run 和 scale-run comparison 消费 batch review summary。
- v254：run decision 消费 scale-run comparison 中的 batch review summary。

所以 v254 是“决策层风险显性化”，不是横向新增一个报告。

## 关键文件

### `src/minigpt/training_scale_run_decision.py`

`build_training_scale_run_decision()` 在遍历 comparison runs 时，为候选和 rejected row 增加：

- `batch_comparison_review_action_count`
- `batch_comparison_blocker_action_count`
- `batch_maturity_coverage_regression_count`

`_decision_summary()` 进一步输出：

- selected run 的 batch review status
- selected run 的 review/blocker/coverage 计数
- comparison 级别的 batch review/blocker/coverage 总数
- coverage-regressed portfolio 名称
- blocker reason 列表

`_batch_review_status()` 把 selected run 归为：

- `clean`：没有 review/blocker/coverage 风险
- `review`：有 review action 或 coverage regression
- `blocker`：有 blocker action
- `missing`：没有选中 run

`_decision_status()` 的边界变化很小：如果 selected run 有 batch blocker action，即使 gate 是 pass，也返回 `review`。这不是禁止执行，而是避免把带 blocker 的证据标成完全 ready。

### `src/minigpt/training_scale_run_decision_artifacts.py`

CSV 新增 selected batch review status、selected review/blocker/coverage 计数，以及 comparison 级别的 batch review/blocker/coverage 总数。

Markdown 和 HTML 在摘要区显示这些字段，rejected runs 表格也显示 review/blocker 计数。这样人工审阅 execute command 时，不需要打开上游 comparison JSON 才能发现 batch risk。

### `tests/test_training_scale_run_decision.py`

新增断言覆盖两类行为：

- 普通 batch review action 会进入 decision summary 和 recommendations。
- 如果 selected run 人为设置为 gate pass 且带 batch blocker action，decision status 会降为 `review`，summary 中 `selected_batch_review_status` 为 `blocker`。

这些测试保护的是 run comparison -> run decision 的字段传递和状态边界。

## 输入输出

输入是 `training_scale_run_comparison.json`。v254 重点消费其中每个 run 的：

- `batch_comparison_review_action_count`
- `batch_comparison_blocker_action_count`
- `batch_maturity_coverage_regression_count`

输出包括：

- `training_scale_run_decision.json`
- `training_scale_run_decision.csv`
- `training_scale_run_decision.md`
- `training_scale_run_decision.html`

这些输出是 execute 前的治理证据，不是模型效果证明。模型能力仍需要真实 checkpoint、固定 suite、scorecard 和 repeated training delta 支撑。

## 测试覆盖

- 聚焦测试覆盖 `training_scale_run_decision`、`training_scale_run_comparison`、`training_scale_run`。
- 全量 unittest 确认既有训练治理、发布治理、评估治理链路没有被字段扩展破坏。
- source encoding 检查确认没有 BOM、不可打印字符或语法错误。

## 运行证据

运行截图和解释归档在 `c/254`：

- `c/254/图片/01-focused-tests.png`
- `c/254/图片/02-structure-check.png`
- `c/254/图片/03-full-unittest.png`
- `c/254/图片/04-source-encoding.png`
- `c/254/解释/说明.md`

## 一句话总结

v254 让 execute decision 从“选择最高 readiness 候选”升级为“选择候选时保留 batch comparison review/blocker 风险”。

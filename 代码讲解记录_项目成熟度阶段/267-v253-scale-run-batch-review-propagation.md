# v253 scale run batch review propagation

## 本版目标和边界

v253 的目标是把 v252 在 `training_portfolio_batch` 中形成的 comparison review 摘要继续向下游传递。上一版已经让 batch 知道自己的 portfolio comparison 是否存在 review action、blocker action、coverage regression 和 blocker reason；本版让 gated scale run 与 scale-run comparison 也能看到这些字段。

本版不改变训练执行逻辑，不改变 gate 放行策略，也不把 review action 默认升级为 blocker。它解决的是证据链断层：如果 batch comparison 已经发现风险，下游 scale-run readiness 或 promotion 输入不能只显示 batch planned/completed，而应该同时保留 review 摘要。

## 前置能力

这条链路来自 v250-v252：

- v250 让 portfolio comparison 消费 maturity coverage regression。
- v251 把 portfolio comparison review action 逻辑拆到独立模块。
- v252 把 comparison review summary 写回 batch execution/report。
- v253 把 batch review summary 传到 scale run 和 scale-run comparison。

所以本版属于“下游证据传播”，不是新的 report-only 横向扩展。

## 关键文件

### `src/minigpt/training_scale_run.py`

`_batch_summary()` 现在从 batch report 的 `comparison_review_summary` 中读取：

- `comparison_review_action_count`
- `comparison_blocker_action_count`
- `maturity_review_count`
- `maturity_coverage_regression_count`
- `maturity_review_names`
- `maturity_coverage_regression_names`
- `comparison_blocker_reasons`
- `comparison_blocker_portfolios`

这些字段进入 scale-run JSON 后，又被 CSV、Markdown、HTML 和 recommendations 消费。这样一个 scale run 作为 promotion 输入时，不只告诉读者“batch 已经运行/计划”，还说明 batch comparison 是否仍有需要人工复核的成熟度或覆盖率风险。

`write_training_scale_run_csv()` 同步增加 review/blocker/coverage 字段，避免机器读取时只看到 JSON 有证据、CSV 缺字段。

### `src/minigpt/training_scale_run_comparison.py`

`_run_summary()` 读取每个 scale run 的 `batch_summary`，把 batch comparison review 字段提升到 run comparison 的行级摘要里。

`_comparison_summary()` 进一步聚合：

- 全部 run 的 batch comparison review action 数
- 全部 run 的 blocker action 数
- coverage regression 总数
- coverage-regressed portfolio 名称
- blocker reason 集合

`_readiness_score()` 对 blocker action 做轻量扣分，recommendations 对 review/blocker action 给出明确提示。这个设计保持了边界：review action 不直接改变 allowed 语义，但会进入 readiness 解释。

### `tests/test_training_scale_run.py`

测试确认：

- review gate 放行的 batch dry-run 会产生 `comparison_review_action_count`
- scale-run recommendations 能提示 review action
- Markdown 和 HTML 渲染包含 review 字段

这些断言保护的是 batch -> scale run 的字段传递。

### `tests/test_training_scale_run_comparison.py`

测试确认：

- scale-run comparison 的 summary 聚合 batch review action
- blocker action 在当前 fixture 下保持为 0
- Markdown 和 HTML 渲染能显示 batch review 字段

这些断言保护的是 scale run -> scale-run comparison 的字段传递。

## 输入输出

输入仍是已有 scale plan、gate profile 和 batch report。batch report 中的 `comparison_review_summary` 是本版新增消费重点。

输出包括：

- scale-run JSON：下游模块读取的主证据。
- scale-run CSV：机器检查和表格消费的轻量索引。
- scale-run Markdown/HTML：人工查看的 release/promotion 证据。
- scale-run comparison JSON/CSV/Markdown/HTML：多个 run 的 readiness 对比证据。

这些输出都是治理证据，不是模型质量本身的证明。模型是否变强仍需要真实 checkpoint、固定 suite、scorecard 和 repeated training delta 支持。

## 测试覆盖

本版验证重点不是训练速度或模型 loss，而是证据字段是否稳定穿过链路：

- 聚焦测试覆盖 `training_scale_run`、`training_scale_run_comparison` 和 `training_portfolio_batch`。
- 全量 unittest 防止字段扩展破坏其他治理链路。
- source encoding 检查防止 CI 再次出现 BOM/不可打印字符/语法错误。

## 运行证据

运行截图和解释归档在 `c/253`：

- `c/253/图片/01-focused-tests.png`
- `c/253/图片/02-structure-check.png`
- `c/253/图片/03-full-unittest.png`
- `c/253/图片/04-source-encoding.png`
- `c/253/解释/说明.md`

这些证据说明 v253 的代码、测试、结构字段和编码卫生形成闭环。

## 一句话总结

v253 让 batch comparison review 不再停留在 batch 报告里，而是成为 scale-run readiness 和 promotion 输入可继续消费的风险信号。

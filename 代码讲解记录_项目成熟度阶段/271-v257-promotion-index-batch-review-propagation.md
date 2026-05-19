# v257 promotion index batch review propagation

## 本版目标和边界

v257 的目标是把 v256 training scale promotion summary 中已经保留下来的 handoff selected batch review/blocker context 继续传到 training scale promotion index。promotion index 是多个 promotion report 汇总成 compare-ready 输入之前的入口，如果这里只显示 `promoted/review/blocked`，就会把“这个 promoted run 是否还带着 selected batch review 风险”隐藏掉。

本版不改变 promoted-only compare 规则：只有 promotion status 为 `promoted` 且 training scale run JSON 存在的报告才进入 `comparison_inputs` 和生成的 compare command。selected batch review/blocker 仍是风险提示和证据上下文，不默认把 promoted run 降级为 review 或 blocked。

## 前置链路

这版延续 v250-v256 的 batch review 证据传播：

- v250-v252：portfolio comparison review action 进入 batch summary。
- v253：batch review/blocker counts 进入 gated scale run 和 scale-run comparison。
- v254：run decision 记录 selected-run batch review status。
- v255：controlled handoff 保留 decision batch review context。
- v256：promotion acceptance 保留 handoff batch review context。
- v257：promotion index 在 promoted-only compare 选择前继续保留这组 context。

它是下游证据传播，不是新的模型能力评估，也不是新的训练策略。

## 关键文件

### `src/minigpt/training_scale_promotion_index_helpers.py`

`_promotion_row()` 现在从 promotion report 的 `summary` 中读取：

- `handoff_selected_batch_review_status`
- `handoff_selected_batch_comparison_review_action_count`
- `handoff_selected_batch_comparison_blocker_action_count`
- `handoff_selected_batch_maturity_coverage_regression_count`
- `handoff_batch_comparison_review_action_count`
- `handoff_batch_comparison_blocker_action_count`
- `handoff_batch_comparison_blocker_reasons`

这些字段不重新计算，只按 promotion summary 原样带入 index row。这样 index row 能同时说明两件事：这个 promotion 是否可作为 compare input，以及它是否仍带有上游 selected batch review/blocker 风险。

`_summary()` 新增聚合字段：

- `handoff_selected_batch_review_count`
- `handoff_selected_batch_blocker_count`
- `handoff_selected_batch_comparison_review_action_total`
- `handoff_selected_batch_comparison_blocker_action_total`
- `handoff_batch_comparison_review_action_total`
- `handoff_batch_comparison_blocker_action_total`
- `handoff_batch_comparison_blocker_reasons`

`_recommendations()` 在 compare-ready 场景下检查这两个计数：

- 存在 selected batch blocker 时，提示先解决 blocker actions，再把 promoted compare inputs 当作 clean evidence。
- 存在 selected batch review 时，提示先复核 review actions。

这条建议不会修改 `comparison_ready_count`，只让人和自动化读者更诚实地理解“promoted 但仍有上游 review 风险”。

### `src/minigpt/training_scale_promotion_index.py`

CSV 新增 handoff batch review 字段列。

Markdown 摘要区新增 selected batch review/blocker 和 batch comparison review/blocker totals；Promotions 表新增 `Batch Review` 和 `Batch Blockers` 两列。

HTML stats cards 和 table 同步显示这些字段，使浏览器页面也能作为人工 review 证据。

### `scripts/index_training_scale_promotions.py`

CLI 输出新增：

- `handoff_selected_batch_review_count`
- `handoff_selected_batch_blocker_count`
- `handoff_batch_comparison_review_action_total`
- `handoff_batch_comparison_blocker_action_total`

这样 CI 日志或命令行 smoke 不必打开 JSON 才能确认 batch review 风险是否被 index 接住。

### `tests/test_training_scale_promotion_index.py`

测试 fixture `make_promotion()` 新增 `selected_batch_review_status` 参数，用 promoted reports 模拟 v256 promotion summary 的输出。

新增测试覆盖：

- promoted reports 带 `blocker/review` batch context 时仍保持 compare-ready。
- index row 保留 selected batch review status 和 blocker action count。
- summary 正确聚合 review/blocker counts、action totals 和 blocker reasons。
- CSV、Markdown、HTML 都暴露新增字段。
- CLI smoke 输出新增 summary totals。

## 输入输出

输入是一个或多个 `training_scale_promotion.json` 或 promotion 目录。

输出仍是：

- `training_scale_promotion_index.json`
- `training_scale_promotion_index.csv`
- `training_scale_promotion_index.md`
- `training_scale_promotion_index.html`

这些输出是 promotion index 证据和 compare command 准备证据，不是模型质量证明。模型质量仍需要后续 promoted comparison、baseline decision、standard suite 和真实 checkpoint delta 证明。

## 测试覆盖

- focused tests 覆盖 promotion index、promotion 和 handoff 三层相邻链路。
- 全量 unittest 确认新增 index 字段没有破坏训练规模、发布治理、server、benchmark 和文档链路。
- source encoding 检查防止 BOM 或语法错误进入 CI。
- 结构检查确认代码、测试、README、讲解和 `c/257` 归档都包含本版关键字段。

## 运行证据

运行截图和解释归档在 `c/257`：

- `c/257/图片/01-focused-tests.png`
- `c/257/图片/02-promotion-index-batch-review-smoke.png`
- `c/257/图片/03-promotion-index-html.png`
- `c/257/图片/04-full-unittest.png`
- `c/257/图片/05-source-encoding.png`
- `c/257/图片/06-docs-check.png`
- `c/257/解释/说明.md`

## 一句话总结

v257 让 promotion index 从“只筛 promoted 输入”升级为“筛 promoted 输入时继续保留 selected batch review/blocker 风险”。

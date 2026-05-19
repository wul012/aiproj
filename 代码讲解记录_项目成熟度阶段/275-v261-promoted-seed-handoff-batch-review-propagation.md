# v261 promoted seed handoff batch review propagation

## 本版目标和边界

v261 的目标是把 v260 promoted next-cycle seed 中已经可见的 handoff selected batch review/blocker context 继续传到 promoted training scale seed handoff。seed handoff 是验证或执行 `plan_training_scale.py` 命令的交接层，如果它只保留 command、suite alignment、clean-evidence readiness 和 plan artifacts，就会把“这个 handoff 是否来自仍带 selected batch review/blocker 风险的 seed”丢掉。

本版不改变 seed handoff 的状态规则。原本是 `planned`、`completed`、`blocked`、`failed` 或 `timeout` 的 handoff 仍按原规则判断；batch review/blocker context 只进入 summary、artifacts、CLI 和 recommendations，用于提醒这个 handoff 还不能被误读为完全干净的模型质量证据。

## 前置链路

这版延续 v250-v260：

- v250-v252：portfolio comparison review action 进入 batch summary。
- v253：batch review/blocker counts 进入 gated scale run 和 run comparison。
- v254：run decision 记录 selected-run batch review status。
- v255：controlled handoff 保留 decision batch review context。
- v256：promotion acceptance 保留 handoff batch review context。
- v257：promotion index 在 promoted-only compare 选择前保留这组 context。
- v258：promoted comparison 在 comparison-ready inputs 上继续保留这组 context。
- v259：promoted baseline decision 在 selected baseline 上继续保留这组 context。
- v260：promoted next-cycle seed 在生成下一轮 plan handoff 时继续保留这组 context。
- v261：promoted seed handoff 在验证或执行 next plan command 时继续保留这组 context。

它是下游证据传播，不是新的训练策略，也不是新的模型能力提升。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff.py`

`_summary()` 现在读取：

- `baseline_seed.handoff_suite_guard`
- `baseline_seed.handoff_batch_review`

前者继续负责 suite boundary；后者新增负责 selected batch review/blocker 风险。

新增进入 summary 的字段包括：

- `selected_handoff_selected_batch_review_status`
- `selected_handoff_selected_batch_comparison_review_action_count`
- `selected_handoff_selected_batch_comparison_blocker_action_count`
- `selected_handoff_selected_batch_maturity_coverage_regression_count`
- `selected_handoff_batch_comparison_review_action_count`
- `selected_handoff_batch_comparison_blocker_action_count`
- `selected_handoff_batch_comparison_blocker_reasons`
- `comparison_ready_handoff_selected_batch_review_count`
- `comparison_ready_handoff_selected_batch_blocker_count`
- `comparison_ready_handoff_selected_batch_comparison_review_action_total`
- `comparison_ready_handoff_selected_batch_comparison_blocker_action_total`
- `comparison_ready_handoff_batch_comparison_review_action_total`
- `comparison_ready_handoff_batch_comparison_blocker_action_total`
- `comparison_ready_handoff_batch_comparison_blocker_reasons`

`_handoff_batch_review_recommendations()` 根据 selected batch review 状态补充 recommendation。selected status 为 `blocker` 时提示先解决 blocker actions；为 `review` 时提示先复核 review actions；如果 selected baseline 干净但其他 comparison-ready promoted inputs 带 blocker，也会保留 review context。

这些 recommendations 被插入到 planned、blocked、timeout、failed 和 completed 路径中，但不改变 handoff 状态。

### `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

CSV 输出新增 selected handoff batch review/blocker 字段和 comparison-ready totals。

Markdown 摘要新增：

- selected handoff batch review
- selected handoff batch review actions
- selected handoff batch blocker actions
- comparison-ready handoff batch review/blocker counts
- comparison-ready blocker reasons

HTML stats cards 同步展示 selected handoff batch、selected blocker actions、ready batch review/blocker counts，让人打开报告即可看到风险。

### `scripts/execute_promoted_training_scale_seed.py`

CLI 输出新增：

- `selected_handoff_selected_batch_review_status`
- `selected_handoff_selected_batch_comparison_review_action_count`
- `selected_handoff_selected_batch_comparison_blocker_action_count`
- `comparison_ready_handoff_selected_batch_review_count`
- `comparison_ready_handoff_selected_batch_blocker_count`
- `comparison_ready_handoff_batch_comparison_blocker_reasons`

这样 CI 日志和人工 smoke 不需要打开 JSON，也能确认 seed handoff 是否接住 seed batch review context。

### `tests/test_promoted_training_scale_seed_handoff.py`

新增测试 `test_carries_seed_handoff_batch_review_into_handoff_outputs_and_script()`。

测试 fixture 里 seed 已 ready，baseline seed 带：

- selected batch review status 为 `blocker`
- selected review action count 为 2
- selected blocker action count 为 1
- blocker reason 为 `coverage-regressed`

handoff 仍保持 `planned`，但测试确认：

- summary 保留 selected 和 comparison-ready context。
- CSV、Markdown、HTML、CLI 都暴露新增字段。
- recommendations 提醒 selected handoff batch blocker actions 需要先解决。

## 输入输出

输入是 `promoted_training_scale_seed.json` 或 promoted seed 目录。

输出仍是：

- `promoted_training_scale_seed_handoff.json`
- `promoted_training_scale_seed_handoff.csv`
- `promoted_training_scale_seed_handoff.md`
- `promoted_training_scale_seed_handoff.html`

这些输出是 seed handoff evidence。它们记录命令验证/执行结果、plan artifacts、suite alignment、clean-evidence readiness 和 batch review context，但本版没有改变 command execution 规则。

## 测试覆盖

- focused tests 覆盖 promoted seed handoff、promoted seed、promoted decision、promoted comparison、promotion index、promotion 和 handoff 相邻链路。
- 全量 unittest 确认新增字段没有破坏其他治理链路。
- source encoding 检查防止 BOM 或语法错误进入 CI。
- Playwright/Chrome 打开 HTML 报告，确认 human-facing report 展示 selected handoff batch 和 ready batch blocker 信息。
- docs check 确认 README、代码讲解、`c/261` 归档和关键字段都同步。

## 运行证据

运行截图和解释归档在 `c/261`：

- `c/261/图片/01-focused-tests.png`
- `c/261/图片/02-promoted-seed-handoff-batch-review-smoke.png`
- `c/261/图片/03-promoted-seed-handoff-html.png`
- `c/261/图片/04-full-unittest.png`
- `c/261/图片/05-source-encoding.png`
- `c/261/图片/06-docs-check.png`
- `c/261/解释/说明.md`

## 一句话总结

v261 让 promoted seed handoff 从“验证或执行 next plan command”升级为“验证/执行 next plan command 时继续保留 selected handoff batch review/blocker 风险”。

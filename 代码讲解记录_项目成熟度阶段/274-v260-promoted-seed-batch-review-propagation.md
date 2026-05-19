# v260 promoted seed batch review propagation

## 本版目标和边界

v260 的目标是把 v259 promoted baseline decision 中已经可见的 handoff selected batch review/blocker context 继续传到 promoted training scale next-cycle seed。promoted seed 是下一轮 `plan_training_scale.py` 命令的交接入口，如果它只保留 selected baseline、suite guard 和 next corpus sources，就会把“这个 next-cycle plan 是否来自仍带 selected batch review/blocker 风险的 baseline”丢掉。

本版不改变 seed readiness 规则。只要 decision 已 accepted、selected run 存在、next corpus sources 存在，原本会 `ready` 的 seed 仍然可以 `ready`；batch review/blocker context 只进入 summary、artifacts、CLI 和 recommendations，用于提醒这个 seed 还不能被误读为完全干净的模型质量证据。

## 前置链路

这版延续 v250-v259：

- v250-v252：portfolio comparison review action 进入 batch summary。
- v253：batch review/blocker counts 进入 gated scale run 和 run comparison。
- v254：run decision 记录 selected-run batch review status。
- v255：controlled handoff 保留 decision batch review context。
- v256：promotion acceptance 保留 handoff batch review context。
- v257：promotion index 在 promoted-only compare 选择前保留这组 context。
- v258：promoted comparison 在 comparison-ready inputs 上继续保留这组 context。
- v259：promoted baseline decision 在 selected baseline 上继续保留这组 context。
- v260：promoted next-cycle seed 在生成下一轮 plan handoff 时继续保留这组 context。

它是下游证据传播，不是新的训练策略，也不是新的模型能力提升。

## 关键文件

### `src/minigpt/promoted_training_scale_seed.py`

`build_promoted_training_scale_seed()` 现在在 `baseline_seed` 中新增：

- `handoff_batch_review`

它和已有的 `handoff_suite_guard` 并列：

- `handoff_suite_guard` 说明 suite boundary 是否一致。
- `handoff_batch_review` 说明 selected baseline 是否带 batch review/blocker 风险。

`_handoff_batch_review()` 从 decision summary 和 selected baseline 两处读取字段，优先使用 summary，缺失时回退到 selected baseline row。它保留：

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

`_summary()` 把这些字段提升到 seed summary，方便 artifacts、CLI、CI 日志和后续 seed handoff 层消费。

`_append_handoff_batch_review_recommendation()` 在 seed `ready` 或 `review` 时补充 recommendation。selected baseline 带 blocker 时提示先解决 blocker actions；带 review 时提示先复核 review actions。它不影响 `seed_status`。

### `src/minigpt/promoted_training_scale_seed_artifacts.py`

CSV 输出新增 selected handoff batch review/blocker 字段和 comparison-ready totals。

Markdown 摘要新增：

- selected handoff batch review
- selected handoff batch review actions
- selected handoff batch blocker actions
- comparison-ready handoff batch review/blocker counts
- comparison-ready blocker reasons

HTML stats cards 和 Baseline Seed section 同步展示 selected handoff batch review、selected blocker actions、comparison-ready blocker count 和 blocker reasons。

### `scripts/build_promoted_training_scale_seed.py`

CLI 输出新增：

- `selected_handoff_selected_batch_review_status`
- `selected_handoff_selected_batch_comparison_review_action_count`
- `selected_handoff_selected_batch_comparison_blocker_action_count`
- `comparison_ready_handoff_selected_batch_review_count`
- `comparison_ready_handoff_selected_batch_blocker_count`
- `comparison_ready_handoff_batch_comparison_blocker_reasons`

这样 CI 日志和人工 smoke 不需要打开 JSON，也能确认 promoted seed 是否接住 decision batch review context。

### `tests/test_promoted_training_scale_seed.py`

新增测试 `test_carries_decision_handoff_batch_review_into_seed_outputs_and_script()`。

测试 fixture 里 decision 已 accepted，selected baseline 为 `beta`，并带：

- selected batch review status 为 `blocker`
- selected review action count 为 2
- selected blocker action count 为 1
- blocker reason 为 `coverage-regressed`

seed 仍保持 `ready`，但测试确认：

- `baseline_seed.handoff_batch_review` 保留 selected context。
- summary 保留 selected 和 comparison-ready context。
- CSV、Markdown、HTML、CLI 都暴露新增字段。
- recommendations 提醒 selected handoff batch blocker actions 需要先解决。

## 输入输出

输入是 `promoted_training_scale_decision.json` 或 promoted decision 目录，加下一轮 corpus sources。

输出仍是：

- `promoted_training_scale_seed.json`
- `promoted_training_scale_seed.csv`
- `promoted_training_scale_seed.md`
- `promoted_training_scale_seed.html`

这些输出是 next-cycle seed evidence。它们会被后续 promoted seed handoff 层消费，但本版没有改变 plan command 的生成规则。

## 测试覆盖

- focused tests 覆盖 promoted seed、promoted decision、promoted comparison、promotion index、promotion 和 handoff 相邻链路。
- 全量 unittest 确认新增字段没有破坏其他治理链路。
- source encoding 检查防止 BOM 或语法错误进入 CI。
- Playwright/Chrome 打开 HTML 报告，确认 human-facing report 展示 selected handoff batch 和 ready batch blocker 信息。
- docs check 确认 README、代码讲解、`c/260` 归档和关键字段都同步。

## 运行证据

运行截图和解释归档在 `c/260`：

- `c/260/图片/01-focused-tests.png`
- `c/260/图片/02-promoted-seed-batch-review-smoke.png`
- `c/260/图片/03-promoted-seed-html.png`
- `c/260/图片/04-full-unittest.png`
- `c/260/图片/05-source-encoding.png`
- `c/260/图片/06-docs-check.png`
- `c/260/解释/说明.md`

## 一句话总结

v260 让 promoted next-cycle seed 从“生成下一轮 plan command”升级为“生成 plan handoff 时继续保留 selected handoff batch review/blocker 风险”。

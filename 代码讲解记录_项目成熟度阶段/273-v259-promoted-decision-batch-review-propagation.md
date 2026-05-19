# v259 promoted decision batch review propagation

## 本版目标和边界

v259 的目标是把 v258 promoted comparison 中已经可见的 handoff selected batch review/blocker context 继续传到 promoted training scale baseline decision。promoted decision 是下一轮 seed 的入口，如果它只保留 selected baseline、readiness、gate、batch 和 suite，就会把“这个 baseline 是否仍带 selected batch review/blocker 风险”丢在上游。

本版不改变 baseline decision 的接受规则。只要 promoted comparison 已完成、selected baseline 满足 readiness/gate/batch/suite 条件，原本会 `accepted` 的决策仍然可以 `accepted`；batch review/blocker context 只进入 summary、artifacts、CLI 和 recommendations，用于提醒它还不能被误读为完全干净的模型质量证据。

## 前置链路

这版延续 v250-v258：

- v250-v252：portfolio comparison review action 进入 batch summary。
- v253：batch review/blocker counts 进入 gated scale run 和 run comparison。
- v254：run decision 记录 selected-run batch review status。
- v255：controlled handoff 保留 decision batch review context。
- v256：promotion acceptance 保留 handoff batch review context。
- v257：promotion index 在 promoted-only compare 选择前保留这组 context。
- v258：promoted comparison 在 comparison-ready inputs 上继续保留这组 context。
- v259：promoted baseline decision 在 selected baseline 上继续保留这组 context。

它是下游证据传播，不是新的评分逻辑，也不是新的模型能力提升。

## 关键文件

### `src/minigpt/promoted_training_scale_decision.py`

`_promotion_rows()` 现在从 promoted comparison row 中读取 handoff batch review 字段：

- `handoff_selected_batch_review_status`
- `handoff_selected_batch_comparison_review_action_count`
- `handoff_selected_batch_comparison_blocker_action_count`
- `handoff_selected_batch_maturity_coverage_regression_count`
- `handoff_batch_comparison_review_action_count`
- `handoff_batch_comparison_blocker_action_count`
- `handoff_batch_comparison_blocker_reasons`

`_summary()` 新增两类字段。

第一类是 selected baseline context：

- `selected_handoff_selected_batch_review_status`
- `selected_handoff_selected_batch_comparison_review_action_count`
- `selected_handoff_selected_batch_comparison_blocker_action_count`
- `selected_handoff_selected_batch_maturity_coverage_regression_count`
- `selected_handoff_batch_comparison_review_action_count`
- `selected_handoff_batch_comparison_blocker_action_count`
- `selected_handoff_batch_comparison_blocker_reasons`

第二类是 comparison-ready aggregate context：

- `comparison_ready_handoff_selected_batch_review_count`
- `comparison_ready_handoff_selected_batch_blocker_count`
- `comparison_ready_handoff_selected_batch_comparison_review_action_total`
- `comparison_ready_handoff_selected_batch_comparison_blocker_action_total`
- `comparison_ready_handoff_batch_comparison_review_action_total`
- `comparison_ready_handoff_batch_comparison_blocker_action_total`
- `comparison_ready_handoff_batch_comparison_blocker_reasons`

这些字段优先消费 promoted comparison summary；当旧输入没有 summary 字段时，再从 promotions 回退计算，保证旧 artifact 仍能被读取。

`_append_handoff_batch_recommendations()` 负责把 selected baseline 的 batch review/blocker 风险写成 recommendation。selected baseline 带 blocker 时提示先解决 blocker actions；带 review 时提示先复核 review actions；如果 selected baseline 干净但其他 comparison-ready promoted inputs 带 blocker，则把它作为对照风险保留。

CSV、Markdown、HTML 输出同步展示这些字段。Markdown 摘要会直接显示 selected handoff batch review、selected blocker actions、comparison-ready blocker counts 和 blocker reasons；HTML stats cards 展示 selected handoff batch 和 ready batch blocker 信息。

### `scripts/decide_promoted_training_scale_baseline.py`

CLI 输出新增：

- `selected_handoff_selected_batch_review_status`
- `selected_handoff_selected_batch_comparison_review_action_count`
- `selected_handoff_selected_batch_comparison_blocker_action_count`
- `comparison_ready_handoff_selected_batch_review_count`
- `comparison_ready_handoff_selected_batch_blocker_count`
- `comparison_ready_handoff_batch_comparison_blocker_reasons`

这样 CI 日志和人工 smoke 不需要打开 JSON，也能确认 promoted decision 是否接住上游 batch review context。

### `tests/test_promoted_training_scale_decision.py`

新增测试 `test_carries_promoted_comparison_handoff_batch_review_into_decision_outputs_and_script()`。

测试 fixture 里有两个 promoted inputs：

- `alpha`：readiness 88，gate warn，带 selected batch review。
- `beta`：readiness 91，gate pass，带 selected batch blocker。

decision 仍选中 `beta` 并保持 `accepted`，但测试确认：

- selected baseline row 保留 `handoff_selected_batch_review_status=blocker`。
- summary 保留 selected blocker action count 和 blocker reasons。
- comparison-ready aggregate counts 仍为 review 1、blocker 1。
- CSV、Markdown、HTML、CLI 都暴露新增字段。
- recommendations 提醒 selected handoff batch blocker actions 需要先解决。

## 输入输出

输入是 `promoted_training_scale_comparison.json` 或 promoted comparison 目录。

输出仍是：

- `promoted_training_scale_decision.json`
- `promoted_training_scale_decision.csv`
- `promoted_training_scale_decision.md`
- `promoted_training_scale_decision.html`

这些输出是 baseline decision evidence。它们会被后续 promoted seed 层消费，但本版没有改变 seed command 生成规则。

## 测试覆盖

- focused tests 覆盖 promoted decision、promoted comparison、promotion index、promotion 和 handoff 相邻链路。
- 全量 unittest 确认新增字段没有破坏其他治理链路。
- source encoding 检查防止 BOM 或语法错误进入 CI。
- Playwright/Chrome 打开 HTML 报告，确认 human-facing report 展示 selected handoff batch 和 ready batch blocker 信息。
- docs check 确认 README、代码讲解、`c/259` 归档和关键字段都同步。

## 运行证据

运行截图和解释归档在 `c/259`：

- `c/259/图片/01-focused-tests.png`
- `c/259/图片/02-promoted-decision-batch-review-smoke.png`
- `c/259/图片/03-promoted-decision-html.png`
- `c/259/图片/04-full-unittest.png`
- `c/259/图片/05-source-encoding.png`
- `c/259/图片/06-docs-check.png`
- `c/259/解释/说明.md`

## 一句话总结

v259 让 promoted baseline decision 从“选择 promoted baseline”升级为“选择 promoted baseline 时继续保留 selected handoff batch review/blocker 风险”。

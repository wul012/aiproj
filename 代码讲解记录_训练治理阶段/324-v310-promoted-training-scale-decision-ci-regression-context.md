# v310 promoted training scale decision CI regression context

## 本版目标和边界

v310 的目标是把 v309 promoted comparison 生成的 CI regression 排除上下文继续传到 promoted baseline decision。
v309 已经知道某些 clean-required promoted inputs 为什么没有进入 comparison；v310 继续解决 decision 层的问题：baseline 选择报告不能只说某个候选被 rejected，还要保留它在 comparison 层被排除的 CI regression 原因。

本版不改变 baseline 选择算法的核心排序，不改变训练、打分或 benchmark 逻辑。
它只把治理证据从 comparison 层继续带入 decision 层，让 rejected candidates、summary、CSV/Markdown/HTML 和 CLI 都能说明 CI-regressed input 为什么没有成为可选 baseline。

## 前置链路

当前链路是：

```text
promotion index
 -> promoted training scale comparison
 -> promoted training scale baseline decision
 -> promoted seed
```

v308 在 index 层排除 CI-regressed clean-required promotions。
v309 在 comparison 层保留排除原因并防御 stale compare-ready index。
v310 则让 decision 层继续消费这些原因，避免决策报告丢掉“为什么没有选它”的证据。

## 关键文件

`src/minigpt/promoted_training_scale_decision.py`

- `_promotion_rows()` 现在读取 `handoff_batch_maturity_ci_regression_count`、`handoff_batch_maturity_ci_regression_names`、`handoff_selected_batch_maturity_ci_regression_count` 和 `comparison_exclusion_reasons`。
- 正常候选的 CI regression 计数会归一为 `0`，避免缺字段时出现 `None` 语义。
- `_rejection_reasons()` 会把 comparison 层的 exclusion reasons 合并进 rejected candidate reasons，并去重。
- clean-required input 如果带 handoff batch CI regression，也会产生 `handoff batch CI regression count is N` 的拒绝理由。

`src/minigpt/promoted_training_scale_decision_review.py`

- `build_decision_handoff_review_summary()` 增加 selected、aggregate、comparison-ready 三组 CI regression counters。
- fallback 统计也改为“clean status 是 clean 且 CI regression count 为 0”才算 clean。
- recommendations 能说明 rejected promoted inputs 里仍有 handoff batch CI regressions。

`src/minigpt/promoted_training_scale_decision_artifacts.py`

- CSV 增加 selected/aggregate/comparison-ready CI regression 字段和 comparison exclusion reasons。
- Markdown/HTML 展示 selected baseline 的 CI regression counters、全量 handoff CI regression、comparison-ready CI regression 和排除原因。

`scripts/decide_promoted_training_scale_baseline.py`

- CLI 输出新增 selected、aggregate、comparison-ready CI regression counters、CI-regressed names 和 exclusion reasons。
- 这样只看 CI 日志也能知道 baseline decision 为什么进入 review。

`tests/test_promoted_training_scale_decision.py`

- 新增 CI-regressed rejected candidate 场景。
- 测试确认 selected baseline 的 CI regression 计数为 0，而 dirty candidate 保留 `comparison_exclusion_reasons` 和 rejected reason。

## 输入输出

输入是 promoted comparison report：

```text
promoted_training_scale_comparison.json
```

v310 关注的输入字段是：

```text
promotions[*].handoff_batch_maturity_ci_regression_count
promotions[*].handoff_batch_maturity_ci_regression_names
promotions[*].handoff_selected_batch_maturity_ci_regression_count
promotions[*].comparison_exclusion_reasons
summary.handoff_batch_maturity_ci_regression_count
summary.comparison_ready_handoff_batch_maturity_ci_regression_count
```

输出仍是：

```text
promoted_training_scale_decision.json
promoted_training_scale_decision.csv
promoted_training_scale_decision.md
promoted_training_scale_decision.html
```

本版新增或继续显式保留：

```text
selected_handoff_batch_maturity_ci_regression_count
selected_handoff_selected_batch_maturity_ci_regression_count
handoff_batch_maturity_ci_regression_count
handoff_selected_batch_maturity_ci_regression_total
comparison_ready_handoff_batch_maturity_ci_regression_count
comparison_ready_handoff_selected_batch_maturity_ci_regression_total
comparison_exclusion_reasons
```

## 核心流程

1. `load_promoted_training_scale_comparison()` 读取 comparison report。
2. `_promotion_rows()` 解析 promotion rows，并保留 comparison 层的 CI regression 字段和 exclusion reasons。
3. `_rejection_reasons()` 根据 compare-ready 状态、clean batch-review requirement、CI regression count、gate、batch 和 readiness 生成 rejected reasons。
4. `_select_candidate()` 仍按 readiness、gate、batch 选择可用 baseline。
5. `build_decision_handoff_review_summary()` 汇总 selected、aggregate、comparison-ready 的 CI regression counters。
6. artifacts 和 CLI 输出同一组字段。

## 静态证据

本版静态证据包含：

- source scan 可看到 promoted decision source、review helper、artifact writer、CLI 和 test 都包含 CI regression 字段。
- rejected candidate reasons 中保留 `handoff batch CI regression count is 2`。
- Markdown/HTML/CSV 都显示 CI regression counters，而不是只有 JSON 可见。

## 测试覆盖

新增测试覆盖：

- comparison report 中存在一个 CI-regressed dirty candidate。
- selected baseline 是 clean candidate，CI regression count 为 0。
- dirty candidate 被 rejected，且 `comparison_exclusion_reasons` 和 rejected `reasons` 都保留 CI regression 原因。
- CSV/Markdown/HTML/CLI 均能看到新字段。

本版还运行 promoted comparison、promoted decision、promoted seed 相邻链路测试，确认 decision 变化没有破坏后续 seed。

## 运行证据

运行截图和解释归档在：

```text
d/310/图片
d/310/解释/说明.md
```

截图覆盖 focused tests、相邻链路 tests、source scan、source encoding、full unittest、docs/git 检查。

## 一句话总结

v310 让 promoted baseline decision 继承 promoted comparison 的 CI regression 排除原因，使 baseline 选择不只给出结果，也保留 rejected candidates 为什么不能进入 clean baseline 的证据。

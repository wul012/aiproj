# v311 promoted training scale seed CI regression context

## 本版目标和边界

v311 的目标是把 v310 promoted baseline decision 中的 CI regression 排除上下文继续带入 promoted next-cycle seed。
v310 已经能让 decision 解释 rejected baseline candidates 为什么被排除；v311 继续保证这个解释不会在生成下一轮 seed 时丢失。

本版不执行训练，不改变 next plan command 的构造逻辑，也不改变 selected baseline。
它只让 seed handoff artifact 保留 selected baseline 是干净的，同时保留 rejected decision inputs 中仍有 handoff batch CI regression 的事实。

## 前置链路

当前链路是：

```text
promoted comparison
 -> promoted baseline decision
 -> promoted next-cycle seed
 -> promoted seed handoff
```

v309 解决 comparison 层排除原因。
v310 解决 decision 层 rejected candidate 解释。
v311 解决 seed 层继续承接这些解释，避免下一轮计划只看到 selected baseline，而看不到被挡在外面的 CI-regressed input。

## 关键文件

`src/minigpt/promoted_training_scale_seed_review.py`

- `build_seed_handoff_clean_batch_review()` 现在读取 selected、aggregate、comparison-ready 三组 CI regression counters。
- `build_seed_handoff_clean_batch_review_summary()` 把这些字段继续写入 seed summary。
- `append_seed_handoff_clean_batch_recommendation()` 会在 rejected decision inputs 存在 handoff batch CI regression 时给出 recommendation。

`src/minigpt/promoted_training_scale_seed_artifacts.py`

- CSV 增加 selected/aggregate/comparison-ready CI regression 字段和 `comparison_exclusion_reasons`。
- Markdown/HTML 展示 handoff batch CI regressions、CI-regressed names 和 comparison exclusion reasons。
- baseline section 同步展示这些字段，方便只看 HTML 时也能定位证据。

`scripts/build_promoted_training_scale_seed.py`

- CLI 输出 selected、aggregate、comparison-ready CI regression counters、CI-regressed names 和 exclusion reasons。
- CI 日志无需打开 JSON 就能看见 seed 是否带着 rejected CI regression context。

`tests/test_promoted_training_scale_seed.py`

- 新增 decision CI regression context fixture。
- 测试确认 seed selected baseline 的 CI regression count 是 0，同时 aggregate 中保留 rejected input 的 CI regression count、names 和 exclusion reasons。

## 输入输出

输入是：

```text
promoted_training_scale_decision.json
```

关键输入字段：

```text
summary.selected_handoff_batch_maturity_ci_regression_count
summary.handoff_batch_maturity_ci_regression_count
summary.handoff_batch_maturity_ci_regression_names
summary.comparison_exclusion_reasons
summary.comparison_ready_handoff_batch_maturity_ci_regression_count
```

输出仍是：

```text
promoted_training_scale_seed.json
promoted_training_scale_seed.csv
promoted_training_scale_seed.md
promoted_training_scale_seed.html
```

本版让这些输出都能看到：

```text
selected_handoff_batch_maturity_ci_regression_count
selected_handoff_selected_batch_maturity_ci_regression_count
handoff_batch_maturity_ci_regression_count
handoff_selected_batch_maturity_ci_regression_total
handoff_batch_maturity_ci_regression_names
comparison_exclusion_reasons
comparison_ready_handoff_batch_maturity_ci_regression_count
comparison_ready_handoff_selected_batch_maturity_ci_regression_total
```

## 核心流程

1. `build_promoted_training_scale_seed()` 读取 decision。
2. `build_seed_handoff_clean_batch_review()` 从 decision summary 和 selected baseline 中继承 clean batch-review 与 CI regression context。
3. `_summary()` 调用 `build_seed_handoff_clean_batch_review_summary()`，把字段提升到 seed summary。
4. artifact writers 输出 JSON/CSV/Markdown/HTML。
5. CLI 打印同一组关键计数和原因。

## 静态证据

本版静态证据包括：

- source scan 能看到 seed review、artifact、CLI、test 全部包含 CI regression 字段。
- seed clean-batch review 子结构保留 `comparison_exclusion_reasons`。
- Markdown/HTML/CSV/CLI 都显示 handoff batch CI regression count，而不只是 JSON 内部字段。

## 测试覆盖

新增测试构造了一个 accepted decision：

- selected baseline 是 clean，selected CI regression count 为 0。
- rejected decision input 中有 handoff batch CI regression count 2。
- seed summary 和 clean-batch review 都保留 `handoff batch CI regression count is 2`。
- CSV/Markdown/HTML/CLI 都能看到新字段。

同时本版跑了 promoted decision、promoted seed、promoted seed handoff 相邻链路测试，确认 seed 改动没有破坏后续 handoff。

## 运行证据

运行截图和解释归档在：

```text
d/311/图片
d/311/解释/说明.md
```

截图覆盖 focused tests、相邻链路 tests、source scan、source encoding、full unittest、docs/git 检查。

## 一句话总结

v311 让 promoted next-cycle seed 不只继承 selected baseline，还继承 rejected decision inputs 的 CI regression 排除解释，从而让下一轮训练计划的起点仍保留完整治理证据。

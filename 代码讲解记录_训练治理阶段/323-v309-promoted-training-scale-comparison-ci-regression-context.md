# v309 promoted training scale comparison CI regression context

## 本版目标和边界

v309 的目标是把 v308 promotion index 里已经识别出的 handoff batch CI regression 证据继续带到 promoted comparison 层。
上一版已经能把 CI-regressed clean-required promotion 排除出 compare inputs；本版继续解决一个更靠后的可解释性问题：promoted comparison 不能只看到“少了一个输入”，还要知道它为什么被排除。

本版不重新设计 promotion index，不改变训练、打分或 baseline delta 算法，也不把 CI regression 当成模型质量指标本身。
它只让 promoted comparison 在消费 index 时保留 guard 证据、输出排除原因，并对旧索引或混合索引做一次防御性复核。

## 前置链路

当前训练治理链路是：

```text
training portfolio comparison
 -> training portfolio batch
 -> training scale run
 -> training scale run comparison
 -> training scale run decision
 -> training scale workflow
 -> training scale handoff
 -> training scale promotion
 -> training scale promotion index
 -> promoted training scale comparison
```

v304-v308 已经把 CI regression 从 batch 一路带到 promotion index。
v309 站在这个索引之后，确保进入 promoted comparison 的输入仍满足 clean batch-review requirement。

## 关键文件

`src/minigpt/promoted_training_scale_comparison.py`

- `_promotion_rows()` 现在读取 `handoff_batch_maturity_ci_regression_count`、`handoff_batch_maturity_ci_regression_names`、`handoff_selected_batch_maturity_ci_regression_count`。
- 新增 `comparison_exclusion_reasons` 字段，说明某个 promoted row 为什么没有进入 comparison。
- `_comparison_exclusion_reasons()` 会检查 promotion 状态、run path 是否存在、clean batch-review 状态，以及 handoff batch CI regression count。
- `_summary()` 区分全量 promotion 行里的 CI regression 统计，以及真正 comparison-ready 行里的 CI regression 统计。
- `_clean_batch_review_guard()` 兼容 row、guard、summary 三种来源，避免旧产物或嵌套字段形态导致证据丢失。

`src/minigpt/promoted_training_scale_comparison_artifacts.py`

- CSV 增加 handoff CI regression 字段和 `comparison_exclusion_reasons`。
- Markdown/HTML 增加全量 handoff CI regression、comparison-ready CI regression、CI-regressed names 和排除原因。
- 这些渲染产物是最终可读证据，不参与模型训练，但会被 CI、人工复查或后续 promoted decision 层读取。

`scripts/compare_promoted_training_scale_runs.py`

- CLI stdout 增加 handoff CI regression 总数、selected 总数、name 列表，以及 comparison-ready 子集统计。
- 这样只看命令日志时，也能知道被比较的 promoted runs 是否仍含 CI-regressed handoff batch。

`tests/test_promoted_training_scale_comparison.py`

- 新增 filtered promoted input 测试：上游 index 已经把 CI-regressed clean-required promotion 排除时，comparison 层要保留原因、统计和渲染字段。
- 新增 stale compare-ready 测试：模拟旧 index 仍把 CI-regressed clean-required promotion 标成 compare-ready，comparison 层必须再次拦住它。

## 输入输出

输入仍是 `training_scale_promotion_index.json` 或其目录。
关键输入字段包括：

```text
promotions[*].promoted_for_comparison
promotions[*].clean_batch_review_guard.handoff_require_clean_batch_review
promotions[*].clean_batch_review_guard.handoff_clean_batch_review_status
promotions[*].handoff_batch_maturity_ci_regression_count
promotions[*].handoff_batch_maturity_ci_regression_names
promotions[*].handoff_selected_batch_maturity_ci_regression_count
```

输出仍是：

```text
promoted_training_scale_comparison.json
promoted_training_scale_comparison.csv
promoted_training_scale_comparison.md
promoted_training_scale_comparison.html
```

其中 JSON/CSV/Markdown/HTML 都会保存：

```text
handoff_batch_maturity_ci_regression_count
handoff_selected_batch_maturity_ci_regression_total
comparison_ready_handoff_batch_maturity_ci_regression_count
comparison_ready_handoff_selected_batch_maturity_ci_regression_total
comparison_exclusion_reasons
```

这些字段的语义是“治理证据”，不是模型分数。
它们用于判断一次 promoted comparison 是否可以作为干净的下一轮 baseline 证据。

## 核心流程

1. `load_training_scale_promotion_index()` 读取 promotion index。
2. `_promotion_rows()` 逐行解析 promotion row，解析 run path 与 clean batch-review guard。
3. `_comparison_exclusion_reasons()` 生成排除原因。
4. 只有 `promoted_for_comparison=true` 且没有排除原因的 row 才进入 `comparison_inputs`。
5. 如果可比较输入不足两个，comparison 状态为 `blocked`，但仍保留全量 promotion 证据。
6. 如果输入足够，则调用 `build_training_scale_run_comparison()`，再把 comparison 结果合并回 promotion rows。
7. artifact writers 输出 JSON/CSV/Markdown/HTML，CLI 输出同样的关键统计。

## 静态证据

本版不是靠 README 声称完成，而是有三层静态证据：

- source scan 可以看到 promoted comparison source、artifact writer、CLI 和 test 都包含 CI regression 字段。
- CSV/Markdown/HTML 渲染字段覆盖全量统计和 comparison-ready 子集统计。
- per-row `comparison_exclusion_reasons` 明确解释被过滤输入，例如 `handoff batch CI regression count is 2`。

## 测试覆盖

重点测试不是简单字段存在，而是两种风险场景：

- 正常 v308+ index：CI-regressed clean-required promotion 已经被上游排除，v309 要把原因和统计继续展示出来。
- 旧索引或混合索引：row 仍标记为 compare-ready，但 handoff batch CI regression count 大于 0，v309 必须再次排除，避免脏输入进入 comparison。

同时本版继续跑 promoted comparison 相邻链路、语法检查、source encoding hygiene 和全量 unittest。

## 运行证据

运行截图与解释归档在：

```text
d/309/图片
d/309/解释/说明.md
```

截图覆盖 focused tests、相邻链路 tests、source scan、source encoding、full unittest、README/讲解索引检查和 git 状态。

## 一句话总结

v309 让 promoted comparison 不再只被动消费 promotion index，而能保留 CI-regressed handoff batch 的过滤原因，并防御旧索引把脏 clean-required 输入误送进 promoted comparison。

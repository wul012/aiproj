# v406 benchmark scorecard suite design readiness

## 本版目标和边界

v406 的目标是把 v405 已经进入 eval suite 报告的 `design_summary` 继续接入 benchmark scorecard 和 benchmark scorecard comparison。这样模型比较不只看生成结果、rubric 分数和 generation-quality flags，还能看到“这套 prompt 本身是否设计完整、是否适合做 checkpoint 比较”。

本版不新增训练流程，不新增模型能力，不创建新的治理链。它把已有 suite-design readiness 融入现有 scorecard 链路，让分数解释更谨慎：如果 prompt suite 设计不适合比较，那么 scorecard 和 cross-run comparison 都要把结论标记为 provisional。

## 前置能力

本版承接两条能力：

- v405：`build_eval_suite_report()` 已经输出 `design_summary`，HTML 也能显示 `Suite Design`。
- 既有 benchmark scorecard：已经整合 eval coverage、generation quality、rubric、pair consistency、pair delta 和 evidence completeness。

v406 做的是把两者接起来：eval suite 的输入质量不再停在 eval report 内，而是进入 scorecard 和 scorecard comparison。

## 关键文件

### `src/minigpt/benchmark_scorecard.py`

新增 `_eval_suite_design_summary()`，读取顺序是：

```text
eval_suite.design_summary
  -> eval_suite.benchmark.design_summary
```

这样兼容 v405 新报告，也兼容把 design summary 放在 benchmark 元数据里的消费者。

`_eval_coverage_component()` 现在同时看两类 readiness：

- `coverage.status`
- `coverage.comparison_status`
- `design_summary.coverage_status`
- `design_summary.comparison_status`

如果 design coverage 不是 `pass`，`eval_coverage` 分数最多 55；如果 design comparison 不是 `pass`，分数最多 75。这个规则的意思是：即使生成样本数和任务覆盖表面上足够，只要 suite design 不适合比较，就不能让 scorecard 像干净 benchmark 一样通过。

summary 新增字段：

```text
eval_suite_design_coverage_status
eval_suite_design_comparison_status
eval_suite_design_duplicate_seed_count
eval_suite_design_expected_behavior_complete
```

recommendations 也新增 suite-design 提示，用来阻止把设计不完整的 prompt suite 当成模型质量提升证据。

### `src/minigpt/benchmark_scorecard_artifacts.py`

Markdown summary 增加：

- Eval coverage
- Eval comparison
- Suite design coverage
- Suite design comparison
- Suite design duplicate seeds

HTML 顶部卡片增加 design coverage 和 design comparison。它们是浏览报告时最先看到的边界信号。

### `src/minigpt/benchmark_scorecard_comparison_deltas.py`

跨 scorecard 比较现在会把 suite-design 字段带入 run summary：

- `eval_suite_design_coverage_status`
- `eval_suite_design_comparison_status`
- `eval_suite_design_duplicate_seed_count`
- `eval_suite_design_expected_behavior_complete`

delta 层新增 changed flag：

- `eval_suite_design_coverage_changed`
- `eval_suite_design_comparison_changed`

summary 层新增：

- `eval_suite_design_readiness_known_count`
- `non_design_comparison_ready_count`
- `non_design_comparison_ready_runs`
- `design_comparison_changed_count`
- baseline design readiness 字段

recommendations 会提示：如果某些 run 不是 suite-design comparison-ready，则 scorecard deltas 只能作为 provisional evidence。

### `src/minigpt/benchmark_scorecard_comparison_artifacts.py`

comparison CSV 增加 suite-design 字段和 changed flags。这样 CI、表格工具或后续 registry 读取时，不必解析 HTML 就能看到 prompt suite 设计边界。

### `src/minigpt/benchmark_scorecard_comparison_sections.py`

Markdown summary 增加 baseline design comparison 和 non design-ready runs；run table 增加 `Design Compare` 列。HTML stats 和 run table 也对应增加 design compare 字段。

## 测试覆盖

本版新增和更新测试覆盖：

- `tests/test_benchmark_scorecard.py`：coverage 已 pass、comparison 已 pass，但 design comparison 为 warn 时，`eval_coverage` 组件降为 warn，score capped 到 75，并产生 suite-design recommendation。
- `tests/test_benchmark_scorecard_artifacts.py`：Markdown/HTML 输出包含 suite design comparison 字段。
- `tests/test_benchmark_scorecard_comparison_deltas.py`：candidate 的 design comparison 从 pass 变 warn 时，delta 记录 changed flag，summary 记录 non-design-ready run，并输出 provisional recommendation。
- `tests/test_benchmark_scorecard_comparison_artifacts.py`：comparison CSV、Markdown、HTML 都包含 suite-design comparison 字段。

这些测试保护的是“输入设计质量必须进入 benchmark 解释”的契约，而不是单纯保护显示文本。

## 运行证据

运行归档在 `d/406`：

- `d/406/解释/说明.md`：本版目标、关键改动和验证命令。
- `d/406/解释/v406-benchmark-scorecard-suite-design-evidence.html`：可浏览证据页。
- `d/406/图片/01-benchmark-scorecard-suite-design-evidence.png`：Playwright MCP 打开的证据页截图。

## 一句话总结

v406 让 benchmark scorecard 在比较模型之前先审查 prompt suite 设计质量，把“题集不够格时分数只能暂定”变成可测试、可渲染、可比较的工程契约。

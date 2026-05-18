# v228 scorecard comparison eval readiness 代码讲解

## 本版目标

v228 的目标是把 benchmark scorecard 的 eval-suite readiness 继续带入跨 scorecard comparison。

v226 让 eval suite 自己输出 readiness；v227 让单个 benchmark scorecard 消费 readiness；v228 负责让多个 scorecard 做对比时继续保留这个边界。

## 不做什么

本版不改变单个 scorecard 的评分。

本版不改变 scorecard decision 的 promote/block 规则。

本版也不把 non-comparison-ready 直接当成阻断项，只在 comparison 报告中做机器可读和人可读提示。

## `src/minigpt/benchmark_scorecard_comparison_deltas.py`

### `summarize_benchmark_scorecard_run()`

run 摘要新增：

```text
eval_suite_coverage_status
eval_suite_comparison_status
```

这些字段来自 v227 的 scorecard summary。这样 comparison 的 `runs[]` 不只记录 overall score、rubric score 和 generation quality flag，也记录 eval 证据是否适合 checkpoint comparison。

### `build_benchmark_scorecard_summary()`

summary 新增：

```text
baseline_eval_suite_coverage_status
baseline_eval_suite_comparison_status
eval_suite_readiness_known_count
non_comparison_ready_count
non_comparison_ready_runs
```

这些字段区分三件事：

- baseline 自己是否 comparison-ready。
- 有多少 run 带有 readiness 证据。
- 哪些参与对比的 run 不是 comparison-ready。

### `build_benchmark_scorecard_recommendations()`

当 `non_comparison_ready_runs` 非空时，推荐语会提示：

```text
Treat scorecard deltas as provisional...
```

如果 baseline 本身不是 comparison-ready，还会提示先换成 comparison-ready baseline，再声称模型质量提升。

这样做不会阻断报告生成，但会避免读者把不干净的 score delta 当成稳健模型改进。

## `src/minigpt/benchmark_scorecard_comparison_artifacts.py`

CSV 输出新增：

```text
eval_suite_coverage_status
eval_suite_comparison_status
```

这让后续表格消费、脚本筛选和人工审阅都能直接看到 readiness 状态。

## `src/minigpt/benchmark_scorecard_comparison_sections.py`

Markdown summary 新增：

```text
Baseline eval comparison
Non comparison-ready runs
```

Runs 表格新增 `Eval Compare` 列。

HTML stats 新增：

```text
Baseline eval compare
Not compare-ready
```

HTML runs 表格也新增 `Eval Compare` 列，同时展示 comparison status 和 coverage status。

## `tests/test_benchmark_scorecard_comparison.py`

测试 fixture `make_scorecard()` 增加 `eval_comparison_status` 参数。

主比较测试把 regressed run 标记为：

```text
eval_suite_comparison_status = warn
```

然后断言：

- summary 的 baseline comparison status 是 `pass`。
- `non_comparison_ready_count == 1`。
- `non_comparison_ready_runs == ["bad"]`。
- recommendations 包含 `not eval-suite comparison-ready: bad`。

artifact 测试继续断言 CSV、Markdown、HTML 都把 readiness 字段渲染出来。

## 输入输出

输入仍然是多个 `benchmark_scorecard.json`。

新消费字段来自 scorecard summary：

```text
eval_suite_coverage_status
eval_suite_comparison_status
```

输出是 comparison JSON/CSV/Markdown/HTML 增量字段，不改变旧核心 delta 字段。

## 运行证据

本版运行证据归档在 `c/228`：

- `图片/01-scorecard-comparison-readiness-tests.png`
- `图片/02-scorecard-comparison-readiness-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v228 是 v226-v227 的下游延伸。

如果只在单个 scorecard 里记录 readiness，到了跨 run 比较时仍可能丢失上下文。v228 把这个上下文带进 comparison 层，让“分数变好了”与“评估是否可比”同时出现。

## 一句话总结

v228 让 cross-scorecard comparison 保留 eval-suite 可比性证据，把模型质量对比从纯分数差推进到带边界的证据差。

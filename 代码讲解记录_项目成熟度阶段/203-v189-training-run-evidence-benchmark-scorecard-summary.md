# v189 training run evidence benchmark scorecard summary

## 本版目标

v189 的目标是把真实训练运行证据继续向 benchmark 层推进：`training_run_evidence` 不只看到训练产物、eval suite 和 generation quality，还能读取 benchmark scorecard 的整体状态、总分和弱项摘要。

它解决的问题是：v188 已经能看到生成质量 flag，但 benchmark scorecard 才是把 eval coverage、generation quality、rubric correctness、pair consistency、pair delta stability 和 evidence completeness 合成一个 run 级评分入口的产物。训练证据如果看不到 scorecard，就还缺一层“这个 run 在综合 benchmark 上处于什么状态”的上下文。

本版明确不做：

- 不改变 benchmark scorecard 的评分规则。
- 不自动修复 scorecard 的弱项。
- 不把 scorecard 分数当成生产级模型能力证明。
- 不把 scorecard 非 pass 当成 checkpoint 缺失；它是 benchmark review 风险。

## 前置路线

v49-v53 建立 benchmark scorecard、drilldown、rubric scoring、registry tracking 和 scorecard comparison。

v137-v141 继续把 generation quality flag taxonomy 和 scorecard promotion decision 接到成熟度叙事。

v186-v188 把真实训练 run evidence 接上 checkpoint、eval suite 和 generation quality。v189 进一步接入 benchmark scorecard，形成：

```text
real train -> eval suite -> generation quality -> benchmark scorecard -> training run evidence
```

## 关键文件

### `src/minigpt/training_run_evidence.py`

`build_training_run_evidence()` 现在会读取：

```text
<run_dir>/benchmark-scorecard/benchmark_scorecard.json
```

并生成新的 `scorecard` section。核心字段包括：

- `exists`：scorecard JSON 是否存在。
- `overall_status`、`overall_score`：综合 benchmark 状态和总分。
- `component_count`：参与评分的组件数量。
- `rubric_status`、`rubric_avg_score`：rubric 正确性状态和平均分。
- `weakest_rubric_case`、`weakest_rubric_score`：最弱 rubric case。
- `weakest_task_type`、`weakest_task_type_score`：最弱任务类型。
- `weakest_difficulty`、`weakest_difficulty_score`：最弱难度组。
- `generation_quality_dominant_flag`、`generation_quality_total_flags`：scorecard 里携带的生成质量风险上下文。

新增 `_scorecard_section()` 只抽取 scorecard 摘要，不重新计算 benchmark 分数。scorecard 的生成、组件权重和 drilldown 仍由 `benchmark_scorecard.py` 负责。

新增 `_scorecard_check()` 的语义：

- scorecard 存在且 `overall_status=pass`：`pass`。
- scorecard 缺失：`warn`。
- scorecard 存在但非 pass：`warn`。

这保留了 evidence 的层次：训练核心产物缺失才是 blocked；benchmark 弱项是 review 风险。

### `src/minigpt/training_run_evidence_artifacts.py`

artifact writer 现在把 `scorecard` section 写入：

- CSV：新增 `benchmark_scorecard_status`、`benchmark_scorecard_score`、`benchmark_scorecard_rubric_status`、`benchmark_scorecard_rubric_avg_score`、`benchmark_scorecard_weakest_task_type`、`benchmark_scorecard_weakest_difficulty`。
- Markdown：新增 `## Benchmark Scorecard` 表格。
- HTML：stats 卡片显示 Scorecard 状态，并新增 Benchmark Scorecard 面板。

这些输出是最终证据，用于让训练 evidence 成为一张更完整的 run review 入口。

### `scripts/build_training_run_evidence.py`

CLI 新增：

```text
benchmark_scorecard_status=<status>
benchmark_scorecard_score=<score>
```

这样终端 smoke 不打开 scorecard HTML，也能看见综合 benchmark 风险。

### `tests/test_training_run_evidence.py`

测试 fixture 新增 `benchmark-scorecard/benchmark_scorecard.json`。

新增断言覆盖：

- 完整 run 的 `scorecard.overall_status` 和 `overall_score` 会进入 report。
- summary 中包含 `benchmark_scorecard_status`。
- 缺 benchmark scorecard 时，run 进入 `review` 而不是 `blocked`。
- Markdown 输出包含 `## Benchmark Scorecard`。

## 运行流程

v189 的真实链路是：

```text
scripts/train.py
 -> scripts/eval_suite.py
 -> scripts/analyze_generation_quality.py
 -> scripts/build_benchmark_scorecard.py
 -> scripts/build_training_run_evidence.py
```

训练证据读取的新增目录结构是：

```text
run_dir/
  benchmark-scorecard/benchmark_scorecard.json
```

## 测试和证据

v189 的截图归档在 `c/189`。

关键验证包括：

- focused tests：覆盖 scorecard pass、scorecard missing review、artifact 输出和 HTML 转义。
- real PyTorch train + eval + generation quality + scorecard smoke：真实跑完整 benchmark 前置链路。
- evidence CLI smoke：输出 benchmark scorecard status 和 score。
- Playwright/Chrome screenshot：确认 Benchmark Scorecard 面板能在浏览器打开。
- source encoding hygiene 和 full unittest discovery：确认新增代码通过全局门禁。

## 边界说明

真实 smoke 中如果 scorecard 因 pair batch 或 evidence completeness 不足而非 pass，training evidence 应该保持 `review`。这不是失败，而是项目现在更诚实：一个 checkpoint 可以训练完成、跑过 eval 和质量分析，但综合 benchmark 仍可能缺少 pair/baseline 等证据。

## 一句话总结

v189 让真实训练 run evidence 能消费 benchmark scorecard 摘要，把单次训练证据推进到“训练、评估、质量和综合 benchmark 风险同屏可审计”的层次。

# v120 benchmark scorecard scoring split 代码讲解

## 本版目标

v120 继续执行 v110 的 module pressure audit 路线，目标是把 `benchmark_scorecard.py` 中已经稳定的评分计算逻辑抽到独立模块：

```text
benchmark_scorecard.py         -> run 证据读取、component 组装、summary、registry context、recommendations、artifact facade
benchmark_scorecard_scoring.py -> case 合并、rubric case scoring、rubric summary、task/difficulty drilldown、评分 helper
```

本版解决的问题是：v114 已经把 benchmark scorecard 的 artifact 输出拆出，但 `benchmark_scorecard.py` 仍然同时承担证据读取、component 汇总、rubric 打分、case 合并、drilldown 聚合和旧导出。v120 把评分层拆出，让 scorecard 主模块从 696 非空行降到 347 非空行。

本版明确不做：

- 不改变 `build_benchmark_scorecard()` 的 schema version 3 输出结构。
- 不改变 rubric check 权重。
- 不改变 task/difficulty drilldown 公式。
- 不改变 `scripts/build_benchmark_scorecard.py` 的 CLI 参数和输出文件名。
- 不改变 `benchmark_scorecard_artifacts.py` 的 JSON/CSV/Markdown/HTML 输出。
- 不改变 `minigpt.benchmark_scorecard` 的旧 public artifact 导出。

## 前置路线

v120 接在这条维护收口路线后面：

```text
v110 module pressure audit
 -> v114 benchmark scorecard artifact split
 -> v118 benchmark scorecard comparison artifact split
 -> v119 maintenance policy artifact split
 -> v120 benchmark scorecard scoring split
```

这说明当前不是重写 benchmark 规则，而是把已经稳定的评分规则放到更清楚的边界里。scorecard 主模块继续编排“从 run 目录读取证据并生成 scorecard”；scoring 模块负责“如何把 case 变成 rubric 和 drilldown 分数”。

## 关键文件

```text
src/minigpt/benchmark_scorecard_scoring.py
src/minigpt/benchmark_scorecard.py
tests/test_benchmark_scorecard_scoring.py
README.md
代码讲解记录_项目成熟度阶段/README.md
c/120/图片
c/120/解释/说明.md
```

`src/minigpt/benchmark_scorecard_scoring.py` 是本版新增的 scoring 层。它负责：

- 从 eval suite、generation quality、pair batch 合并 case 行。
- 按 rubric 计算每个 case 的 required terms、forbidden terms、length bounds、task shape 和最终分数。
- 汇总 rubric summary。
- 把 rubric 结果回填到 case scores。
- 生成 task type 和 difficulty drilldown。

`src/minigpt/benchmark_scorecard.py` 仍然是旧 public API 和 CLI 依赖的主模块。它继续负责：

- 读取 `eval_suite.json`、`generation_quality.json` 和 `pair_generation_batch.json`。
- 计算 eval coverage、generation quality、rubric correctness、pair consistency、pair delta stability 和 evidence completeness components。
- 组装 summary、registry context、recommendations 和 warnings。
- 通过原有函数名委托 artifact 输出。

## 核心数据结构

scoring 模块的输入是三个报告对象：

- `eval_suite.results`：prompt、generated、continuation、expected_behavior、rubric、char_count、task_type、difficulty。
- `generation_quality.cases`：case status、unique_ratio、flag_count。
- `pair_batch.results`：left/right 生成对比中的 equality 和 char delta。

`case_scores()` 输出合并后的 case rows，每个 row 可能包含：

- `name`
- `task_type`
- `difficulty`
- `prompt`
- `generated`
- `continuation`
- `expected_behavior`
- `rubric`
- `generation_quality_status`
- `pair_generated_equal`
- `pair_generated_char_delta`

`rubric_scores()` 输出：

- `summary.case_count`
- `summary.avg_score`
- `summary.overall_status`
- `summary.pass_count` / `warn_count` / `fail_count`
- `summary.weakest_case`
- `cases`

`benchmark_drilldowns()` 输出：

- `task_type`
- `difficulty`
- `weakest_task_type`
- `weakest_difficulty`

这些字段仍被 `benchmark_scorecard.py` 原样写入最终 scorecard。

## 核心函数

`case_scores(eval_suite, generation_quality, pair_batch)`

把三类输入按 case name 合并。它不读取文件，只处理已经读入的 dict。排序仍按 case name 稳定输出。

`rubric_case_score(case)`

执行单个 case 的 rubric 检查：

- `has_output`：生成文本非空。
- `length_bounds`：字符长度满足 min/max。
- `must_include`：required terms 是否出现。
- `must_avoid`：forbidden terms 是否未出现。
- `task_shape`：structured/summary/普通任务的形态是否合理。

权重保持不变：0.2、0.2、0.25、0.15、0.2。

`rubric_scores(case_rows)`

对所有 case 计算 rubric，并汇总 avg score、整体 status、pass/warn/fail 数和 weakest case。

`case_scores_with_rubric(case_rows, rubric_report)`

把 rubric score/status/failed checks/missing terms 回填到 case rows，供 scorecard artifact 和 drilldown 使用。

`benchmark_drilldowns(case_rows)`

分别按 `task_type` 和 `difficulty` 聚合，输出每组的 coverage、rubric、generation quality、pair consistency、pair delta stability 和最终 group score。

## 输入输出边界

v120 后的运行流程是：

```text
run_dir evidence JSON files
 -> benchmark_scorecard.py 读取证据
 -> benchmark_scorecard_scoring.case_scores()
 -> benchmark_scorecard_scoring.rubric_scores()
 -> benchmark_scorecard_scoring.case_scores_with_rubric()
 -> benchmark_scorecard_scoring.benchmark_drilldowns()
 -> benchmark_scorecard.py 组装 scorecard schema v3
 -> benchmark_scorecard_artifacts.py 写 JSON/CSV/Markdown/HTML
```

scoring 模块不写文件、不读取 run 目录、不生成 artifact。它只接收 dict/list 并返回 dict/list，因此它可以被单独测试，也不会改变 CLI 行为。

## 测试覆盖

`tests/test_benchmark_scorecard_scoring.py` 新增两类断言：

- 直接调用 scoring 模块，从 eval/generation/pair 输入构建 case rows、rubric summary、scored cases 和 task/difficulty drilldowns。
- 直接调用 `rubric_case_score()`，锁住 missing required terms、forbidden terms 和 warn status 的真实规则。

原有 `tests/test_benchmark_scorecard.py` 继续覆盖：

- `build_benchmark_scorecard()` 合并 components、rubric、drilldowns、registry context 和 warnings。
- `write_benchmark_scorecard_outputs()` 的 JSON/CSV/drilldown CSV/rubric CSV/Markdown/HTML 文件。
- HTML escaping。

回归测试继续覆盖 artifact 模块和 comparison 模块，确保拆 scoring 后 scorecard 仍能被后续 comparison 消费。

## 运行证据

v120 的运行证据放在：

```text
c/120/图片
c/120/解释/说明.md
```

截图覆盖新增 scoring 单测、旧 benchmark scorecard 回归、compileall、全量 unittest、CLI smoke、输出文件检查、Playwright/Chrome 打开 HTML、README/阶段索引/c README 检查。

README 更新了当前版本、版本标签、结构树和截图索引。阶段 README 追加了 `135-v120-benchmark-scorecard-scoring-split.md`，说明这次拆分属于项目成熟度阶段的评估评分层维护收口。

## 一句话总结

v120 把 benchmark scorecard 从“证据读取、评分计算和输出衔接集中在一个模块”推进到“scorecard orchestration 与 scoring logic 分离”的维护状态，让 benchmark 规则更容易单独验证和继续演进。

# 第一百一十四版代码讲解：Benchmark Scorecard Artifact Split

## 本版目标

v114 的目标是继续落实 v110 的 `module pressure audit`，把 `benchmark_scorecard.py` 中已经稳定的输出/渲染层抽成独立模块 `benchmark_scorecard_artifacts.py`。
这版不是新增 benchmark 功能，也不是修改评分口径，而是把 JSON、CSV、Markdown、HTML 这类 artifact 写出逻辑从评分核心里分离出来，让 `benchmark_scorecard.py` 更专注于“怎么评分”，让新模块专注于“怎么输出证据”。

本版明确不做：
- 不修改 `benchmark_scorecard.json` 的 schema。
- 不修改 overall score、rubric score、drilldown score 的计算公式。
- 不修改 `scripts/build_benchmark_scorecard.py` 的 CLI 参数和输出文件名。
- 不修改 benchmark scorecard comparison。
- 不回改 v49-v53 的历史标签和旧证据。

## 路线来源

本版来自 v110-v113 的厚模块治理路线：

```text
v110 module pressure audit
 -> benchmark_scorecard.py remains a large evaluation module
 -> v111 registry asset split separates display assets
 -> v112 pair artifact split separates saved pair evidence
 -> v113 request history split separates inference log evidence
 -> v114 benchmark scorecard artifact split separates benchmark output evidence
```

`benchmark_scorecard.py` 适合这一版拆分，因为它同时承担两种职责：
- 评分核心：读取 eval/generation/pair/registry，计算 component、rubric、drilldown、summary。
- 证据输出：写 JSON/CSV/Markdown/HTML，渲染 HTML 卡片和 Markdown 表格。

v114 只抽第二类职责，不触碰第一类职责。

## 关键文件

- `src/minigpt/benchmark_scorecard_artifacts.py`
  - 新增模块。
  - 承接 benchmark scorecard 的 JSON/CSV/Markdown/HTML 写出和渲染。
- `src/minigpt/benchmark_scorecard.py`
  - 保留 `build_benchmark_scorecard()` 和评分 helper。
  - 原 public writer/render 函数继续存在，但内部委托给 `benchmark_scorecard_artifacts.py`。
- `tests/test_benchmark_scorecard_artifacts.py`
  - 新增 artifact 层测试。
  - 直接覆盖 HTML escaping、Markdown sections、CSV headers、输出文件集合和 wrapper delegation。
- `tests/test_benchmark_scorecard.py`
  - 原 scorecard builder 回归继续证明评分 schema 和输出契约不变。
- `tests/test_benchmark_scorecard_comparison.py`
  - 继续证明 comparison 层能消费 scorecard JSON。
- `README.md`、`c/114`、本讲解文件
  - 保存本版目标、运行证据和版本解释。

## 核心数据结构

输入仍然是 `build_benchmark_scorecard()` 生成的 scorecard dict：

```json
{
  "schema_version": 3,
  "summary": {
    "overall_status": "pass",
    "overall_score": 91.25,
    "rubric_status": "pass",
    "task_type_group_count": 4
  },
  "components": [],
  "rubric_scores": {},
  "drilldowns": {},
  "case_scores": [],
  "registry_context": {},
  "recommendations": [],
  "warnings": []
}
```

v114 不改变这份数据，只改变谁负责把它写成文件。

## 核心函数

`write_benchmark_scorecard_outputs(scorecard, out_dir)`

统一写出六类产物：

```text
benchmark_scorecard.json
benchmark_scorecard.csv
benchmark_scorecard_drilldowns.csv
benchmark_scorecard_rubric.csv
benchmark_scorecard.md
benchmark_scorecard.html
```

它是 CLI 和训练组合流水线最常用的输出入口。

`render_benchmark_scorecard_markdown(scorecard)`

负责 Markdown 证据，包含：
- Summary
- Components
- Task Type Drilldown
- Difficulty Drilldown
- Rubric Scores
- Case Scores
- Recommendations
- Warnings

`render_benchmark_scorecard_html(scorecard)`

负责 HTML 证据，包含：
- 顶部指标卡
- benchmark components
- rubric scores
- task/difficulty drilldowns
- case scores
- registry context
- recommendations/warnings

所有可变文本都会走 HTML escape，避免 `<Benchmark>` 这类标题被浏览器当成标签。

`write_benchmark_scorecard_csv()`、`write_benchmark_scorecard_drilldown_csv()`、`write_benchmark_scorecard_rubric_csv()`

分别输出 component、drilldown、rubric 三类表格，用于后续比较、归档和人工检查。

## 运行流程

CLI 流程保持不变：

```text
scripts/build_benchmark_scorecard.py
 -> build_benchmark_scorecard()
 -> write_benchmark_scorecard_outputs()
 -> benchmark_scorecard_artifacts.write_benchmark_scorecard_outputs()
 -> JSON/CSV/Markdown/HTML files
```

外部调用者仍然可以从 `minigpt.benchmark_scorecard` 导入：
- `render_benchmark_scorecard_html`
- `render_benchmark_scorecard_markdown`
- `write_benchmark_scorecard_outputs`

因此这版是内部责任边界变化，不是外部 API 变化。

## 为什么这是轻量质量优化

`benchmark_scorecard.py` 原本约 1224 行，既有评分计算，又有 HTML/Markdown/CSV 渲染。v114 后：
- `benchmark_scorecard.py` 降到约 816 行。
- `benchmark_scorecard_artifacts.py` 承接约 430 行输出层。
- 评分逻辑没有改公式。
- 输出文件名和字段契约没有改。

这比继续新增 report-only 小功能更有维护价值，因为后续想调整 scorecard 展示样式、CSV 列或 Markdown 结构时，不会碰到评分核心。

## 测试覆盖

`tests/test_benchmark_scorecard_artifacts.py` 覆盖：
- HTML 会 escape `<Benchmark>`。
- HTML 包含 Benchmark Components、Rubric Scores、Task Type Drilldown。
- Markdown 包含 Components、Rubric Scores、Difficulty Drilldown。
- 输出文件集合固定为 JSON、CSV、drilldowns CSV、rubric CSV、Markdown、HTML。
- CSV header 保持既有契约。
- `benchmark_scorecard.py` 的 public wrapper 与 artifact 模块输出一致。

`tests/test_benchmark_scorecard.py` 继续覆盖：
- schema version 仍为 3。
- overall/rubric/drilldown summary 不变。
- builder 能生成完整 output set。

`tests/test_benchmark_scorecard_comparison.py` 继续覆盖：
- 多 scorecard comparison 仍能读取和比较 scorecard JSON。

## 证据闭环

v114 证据放在 `c/114`：
- `01-unit-tests.png`: artifact tests、scorecard regression、comparison、compileall 和全量 unittest。
- `02-benchmark-artifact-smoke.png`: 行数下降、scorecard output smoke 和 module pressure smoke。
- `03-benchmark-artifact-structure-check.png`: 新模块、测试、README、讲解和 c 归档结构对齐。
- `04-benchmark-artifact-output-check.png`: JSON/CSV/Markdown/HTML 输出和 wrapper parity 检查。
- `05-playwright-benchmark-scorecard-html.png`: scorecard HTML 在真实 Chrome 中渲染。
- `06-docs-check.png`: README、c/114、代码讲解和索引检查。

这些证据是最终归档；临时 run、临时 HTML、测试缓存和 `__pycache__` 在完成前清理。

## 一句话总结

v114 把 benchmark scorecard 的证据输出层从评分核心中抽离，让模型评估模块更清楚地区分“评分计算”和“证据发布”。

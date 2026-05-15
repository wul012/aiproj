# v118 benchmark comparison artifact split 代码讲解

## 本版目标

v118 继续执行 v110 的 module pressure audit 路线，目标是把 `benchmark_scorecard_comparison.py` 中已经稳定的输出写入和页面渲染逻辑抽到独立模块：

```text
benchmark_scorecard_comparison.py           -> scorecard 读取、baseline 选择、run/case/group delta 计算、summary、recommendations、CLI
benchmark_scorecard_comparison_artifacts.py -> JSON/CSV/case-delta CSV/Markdown/HTML 输出和展示 helper
```

本版解决的问题是：`benchmark_scorecard_comparison.py` 已经承担“比较计算”和“证据发布”两类职责。v114 已经证明 benchmark scorecard 的评分计算和 artifact 输出可以分离，v118 把同样的边界应用到跨 run scorecard comparison，让比较模块从 781 行降到 425 行，同时让输出层可以单独测试。

本版明确不做：

- 不改变 `build_benchmark_scorecard_comparison()` 生成的 report schema。
- 不改变 `scripts/compare_benchmark_scorecards.py` 的 CLI 契约和默认输出文件名。
- 不改变 JSON、CSV、case delta CSV、Markdown、HTML 的文件名。
- 不改变 `minigpt.benchmark_scorecard_comparison` 的旧 public artifact 导出。
- 不新增模型训练、benchmark 评分规则或真实 checkpoint 评估能力。

## 前置路线

v118 接在这条维护收口路线后面：

```text
v110 module pressure audit
 -> v114 benchmark scorecard artifact split
 -> v116 registry data/render split
 -> v117 server contract split
 -> v118 benchmark scorecard comparison artifact split
```

这说明当前不是继续堆 report 变体，而是在已有评估治理链路上做轻量、定向的职责分离。benchmark scorecard comparison 的核心价值仍然是比较多个 scorecard；artifact 模块只负责把同一份 comparison report 发布成可检查的证据。

## 关键文件

```text
src/minigpt/benchmark_scorecard_comparison_artifacts.py
src/minigpt/benchmark_scorecard_comparison.py
tests/test_benchmark_scorecard_comparison_artifacts.py
README.md
代码讲解记录_项目成熟度阶段/README.md
c/118/图片
c/118/解释/说明.md
```

`src/minigpt/benchmark_scorecard_comparison_artifacts.py` 是本版新增的 artifact 层。它负责把已经计算好的 comparison report 写成 JSON、CSV、case delta CSV、Markdown 和 HTML。这个模块不读取 scorecard 文件，也不决定 baseline，不计算 best/worst run，只消费上游传入的 report 字典。

`src/minigpt/benchmark_scorecard_comparison.py` 仍然是旧 public API 和 CLI 依赖的主模块。它继续负责 `load_scorecards()`、baseline 解析、run summary、baseline delta、case delta、task type delta、difficulty delta、summary 和 recommendations。它从新 artifact 模块导入旧函数名，所以旧代码继续写：

```python
from minigpt.benchmark_scorecard_comparison import write_benchmark_scorecard_comparison_outputs
```

不会被破坏。

`tests/test_benchmark_scorecard_comparison_artifacts.py` 是新增测试。它直接导入 artifact 模块，验证 artifact 模块可以独立消费 report，并验证旧 facade 导出仍然指向新实现。

## 核心数据结构

artifact 模块消费的核心输入是 comparison report 字典。关键字段包括：

- `title`：报告标题，用于 Markdown/HTML 页面标题和 JSON 元数据。
- `generated_at`：生成时间，写入所有可读证据。
- `runs`：每个 scorecard run 的 summary、overall score、pass rate、case count、case status counts 和 rubric averages。
- `baseline`：baseline run 的 id/name/path。
- `baseline_deltas`：每个 run 相对 baseline 的 overall score、pass rate、case count、case status 和 rubric average delta。
- `case_deltas`：逐 case 的 status/rubric/missing terms delta。
- `task_type_deltas` / `difficulty_deltas`：按任务类型和难度聚合的 delta。
- `summary`：best run、worst run、spread、baseline index、improved/regressed/unchanged counts。
- `recommendations`：后续操作建议。

这些字段仍由 `benchmark_scorecard_comparison.py` 计算。v118 只改变这些字段进入文件系统和 HTML 页面的位置。

## 核心函数

`write_benchmark_scorecard_comparison_json(report, path)`
把 comparison report 原样写成 JSON。它是最完整的机器可读证据，后续模块如果要消费 comparison 结果，应该优先读取这个文件。

`write_benchmark_scorecard_comparison_csv(report, path)`
把 run-level comparison 写成 CSV。它展开 `runs` 和 `baseline_deltas`，保留 `overall_score_delta`、`pass_rate_delta`、`case_count_delta`、`rubric_avg_score_delta` 等字段，适合表格查看和人工对比。

`write_benchmark_scorecard_case_delta_csv(report, path)`
把 `case_deltas` 写成逐 case CSV。它保留 `status_changed`、`rubric_avg_score_delta`、`missing_terms_delta`、`added_missing_terms` 和 `removed_missing_terms`，用于解释某个 run 为什么相对 baseline 变好或变差。

`render_benchmark_scorecard_comparison_markdown(report)`
把同一份 report 渲染成 Markdown。它会展示 run overview、summary、baseline deltas、case deltas、group deltas 和 recommendations。

`render_benchmark_scorecard_comparison_html(report)`
把 report 渲染成 HTML。它负责 HTML escaping、表格样式、状态 class、summary cards 和可读分区。这里的 HTML 是最终证据页面，不是临时预览文件。

`write_benchmark_scorecard_comparison_outputs(report, out_dir)`
统一写出五类文件，并返回路径索引：

```json
{
  "json": ".../benchmark_scorecard_comparison.json",
  "csv": ".../benchmark_scorecard_comparison.csv",
  "case_delta_csv": ".../benchmark_scorecard_case_deltas.csv",
  "markdown": ".../benchmark_scorecard_comparison.md",
  "html": ".../benchmark_scorecard_comparison.html"
}
```

## 输入输出边界

v118 后的运行流程是：

```text
scorecard JSON files
 -> benchmark_scorecard_comparison.load_scorecards()
 -> build_benchmark_scorecard_comparison()
 -> comparison report dict
 -> benchmark_scorecard_comparison_artifacts.write_*()
 -> JSON/CSV/case CSV/Markdown/HTML evidence
```

artifact 输出是最终证据，而不是临时调试产物。JSON 用于后续机器消费，CSV/case CSV 用于表格检查，Markdown/HTML 用于展示和截图归档。artifact 模块不反向影响 scorecard 计算，因此拆分风险主要集中在“输出是否保持一致”和“旧导入是否仍然可用”。

## 测试覆盖

`tests/test_benchmark_scorecard_comparison_artifacts.py` 新增两类断言：

- 直接调用 `write_benchmark_scorecard_comparison_outputs()`，确认 JSON、CSV、case delta CSV、Markdown 和 HTML 都能写出，并且 CSV header、case delta 字段、Markdown section 和 HTML escaping 都存在。
- 验证 `minigpt.benchmark_scorecard_comparison` 中的旧 artifact 函数与 `benchmark_scorecard_comparison_artifacts` 中的新函数是同一对象，锁住 facade parity。

回归测试继续覆盖：

- `tests.test_benchmark_scorecard_comparison`
- `tests.test_benchmark_scorecard`
- `tests.test_benchmark_scorecard_artifacts`

全量 `unittest discover` 也通过，说明这次拆分没有破坏其他治理链路。

## 运行证据

v118 的运行证据放在：

```text
c/118/图片
c/118/解释/说明.md
```

截图覆盖新增 artifact 单测、旧 comparison 回归、compileall、全量 unittest、维护压力 smoke、输出文件检查、Playwright/Chrome 打开 HTML、README/阶段索引/c README 检查。

README 更新了当前版本、版本标签、结构树和截图索引。阶段 README 追加了 `133-v118-benchmark-comparison-artifact-split.md`，说明这次拆分属于项目成熟度阶段的评估比较链路维护收口。

## 一句话总结

v118 把 benchmark scorecard comparison 从“比较计算和证据发布混在一个模块”推进到“comparison logic 与 artifact rendering 分离”的维护状态，让评估比较链路更容易继续扩展和验证。

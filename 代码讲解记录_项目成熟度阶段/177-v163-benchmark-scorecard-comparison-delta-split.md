# v163 benchmark scorecard comparison delta split 代码讲解

## 本版目标

v163 的目标是把 `benchmark_scorecard_comparison.py` 里的 run delta、case delta、task/difficulty group delta、summary、recommendation 和 best-run 选择拆到独立模块 `benchmark_scorecard_comparison_deltas.py`。

它解决的问题是：scorecard comparison 在 v139 以后同时承担加载、命名、baseline 选择、delta 计算、summary 聚合、recommendation 输出和 artifact facade 导出，虽然 artifact 层已经拆过，但主入口仍然偏宽。本版把“比较计算”从“入口编排”里拿出来，让主模块只保留对外 API 和文件、名称、baseline 入口逻辑。

本版明确不做：

- 不改 `benchmark_scorecard_comparison.json` schema。
- 不改 `scripts/compare_benchmark_scorecards.py` 的使用方式。
- 不改 `benchmark_scorecard_comparison_artifacts.py` 的 JSON/CSV/Markdown/HTML 输出。
- 不改 `benchmark_scorecard_decision.py` 对 comparison payload 的消费方式。
- 不引入新的 benchmark 评分指标或模型训练逻辑。

## 前置路线

这版承接两条已经形成的维护路线：

- v53-v54 建立 benchmark scorecard comparison 和 artifact 归档。
- v139-v141 增加 generation-quality flag taxonomy、cross-scorecard delta 和 scorecard promotion decision。
- v153-v162 连续把 release、server、registry、training scale、dataset card、model card 的输出层或 helper 层拆开。

v163 不是继续拆一个新的报告格式，而是回到当前最大模块，把 scorecard comparison 的核心计算边界独立出来。

## 关键文件

- `src/minigpt/benchmark_scorecard_comparison.py`：保留公开入口 `load_benchmark_scorecard()` 和 `build_benchmark_scorecard_comparison()`，负责读取 scorecard、解析名称、选择 baseline、组装最终 report，并继续 re-export artifact 写出函数。
- `src/minigpt/benchmark_scorecard_comparison_deltas.py`：新增纯计算模块，负责 run summary、run delta、case delta、task/difficulty group delta、summary、recommendation 和 best-run 选择。
- `tests/test_benchmark_scorecard_comparison_deltas.py`：新增直接测试，验证 delta 模块不只通过整体 comparison 间接覆盖。
- `tests/test_benchmark_scorecard_comparison.py`：继续覆盖外部 comparison schema 和 artifact 输出使用链路。
- `tests/test_benchmark_scorecard_comparison_artifacts.py`：继续保护旧 facade 导出和 artifact 写出行为。
- `tests/test_benchmark_scorecard_decision.py`：继续证明 scorecard promotion decision 能消费拆分后的 comparison payload。
- `README.md`、`c/README.md`、`c/163/解释/说明.md`、本讲解文件：记录版本目标、运行证据和 tag 含义。

## 核心数据结构

`build_benchmark_scorecard_comparison()` 的输出 schema 没变，仍包含：

- `runs`：每个 scorecard 的摘要，包含 overall score、rubric 平均分、case 数、generation-quality flag 数、weakest case 等。
- `baseline`：用于比较的基准 run。
- `baseline_deltas`：每个 run 相对 baseline 的总体分数、rubric 分数、flag 数和 weakest-case 变化。
- `case_deltas`：每个 benchmark case 的 rubric score delta、missing terms 和 failed checks 变化。
- `task_type_deltas`：按 task type 聚合的分数变化。
- `difficulty_deltas`：按难度聚合的分数变化。
- `summary`：把上述 delta 聚合成 regression/improvement 计数和最弱回归点。
- `recommendations`：基于 summary 和 delta 生成的人读建议。
- `best_by_overall_score` / `best_by_rubric_avg_score`：用于后续判断的最佳 run 摘要。

## 核心函数

`benchmark_scorecard_comparison.py` 现在的主流程是：

```text
scorecard paths
 -> load_benchmark_scorecard()
 -> _resolve_names()
 -> summarize_benchmark_scorecard_run()
 -> _select_baseline()
 -> build_benchmark_scorecard_run_delta()
 -> build_benchmark_scorecard_case_deltas()
 -> build_benchmark_scorecard_group_deltas(task_type/difficulty)
 -> build_benchmark_scorecard_summary()
 -> build_benchmark_scorecard_recommendations()
 -> final comparison payload
```

`benchmark_scorecard_comparison_deltas.py` 的关键函数分工：

- `summarize_benchmark_scorecard_run()`：从单个 scorecard 里抽出 run-level 摘要，屏蔽 summary、rubric_scores、drilldowns 的结构差异。
- `build_benchmark_scorecard_run_delta()`：比较单个 run 和 baseline 的 overall、rubric、flag、weakest-case 变化。
- `build_benchmark_scorecard_case_deltas()`：对齐 baseline 和候选 scorecard 的 case 集合，输出逐 case delta。
- `build_benchmark_scorecard_group_deltas()`：对齐 task type 或 difficulty 维度，输出 group-level delta。
- `build_benchmark_scorecard_summary()`：把 run/case/group delta 汇总成 regression/improvement 计数和最弱回归定位。
- `build_benchmark_scorecard_recommendations()`：把结构化 summary 转成人读建议。
- `select_best_benchmark_scorecard_run()`：按指定字段选择最佳 run，保留原 report 的 best-by 字段语义。

## 输入输出边界

输入仍是一个或多个 `benchmark_scorecard.json`，可以传文件，也可以传 run 目录。

输出仍是 comparison payload；artifact 写出仍由 `benchmark_scorecard_comparison_artifacts.py` 负责。v163 新模块不写文件、不渲染 HTML、不生成 Markdown，只做结构化计算。因此它更容易被单测覆盖，也更容易被未来 decision、maturity narrative 或 registry 消费。

## 测试覆盖

本版测试分四层：

- `tests.test_benchmark_scorecard_comparison`：验证完整 comparison report 的 run/case/group delta、summary 和 artifact 输出仍正常。
- `tests.test_benchmark_scorecard_comparison_artifacts`：验证 artifact 模块写出 JSON/CSV/case CSV/Markdown/HTML，并保护旧 facade 导出。
- `tests.test_benchmark_scorecard_comparison_deltas`：直接构造两个 scorecard 字典，断言 run delta、case delta、group delta、summary、recommendation、best-run 选择都符合预期。
- `tests.test_benchmark_scorecard_decision`：验证 promotion decision 仍能读取并消费 comparison payload。

全量 `unittest discover` 作为回归网，覆盖模型、训练、server、registry、release、maturity 和 benchmark 链路。

## 产物和证据

`c/163/图片/` 保存本版运行截图：

- `01-benchmark-delta-tests.png`：局部 benchmark comparison/delta/decision 测试。
- `02-benchmark-delta-smoke.png`：delta 模块直接 smoke。
- `03-maintenance-smoke.png`：维护批处理与 module pressure 检查。
- `04-source-encoding-smoke.png`：源码编码和 Python 3.11 语法兼容检查。
- `05-full-unittest.png`：全量单测。
- `06-docs-check.png`：README、归档、讲解、源码和测试关键词一致性检查。

这些截图是最终证据，临时日志和临时 run 输出完成后按 AGENTS 清理。

## 行数变化

- `src/minigpt/benchmark_scorecard_comparison.py`：从 549 行降到 134 行。
- `src/minigpt/benchmark_scorecard_comparison_deltas.py`：441 行，集中承载纯比较计算。

这个变化不是为了让总行数减少，而是把入口编排、artifact 输出和 delta 计算分开，让每个模块的职责更稳定。

## 一句话总结

v163 把 benchmark scorecard comparison 的“入口编排”和“delta 计算”拆开，让 benchmark 治理链路在 schema 不变的前提下更容易维护和继续扩展。

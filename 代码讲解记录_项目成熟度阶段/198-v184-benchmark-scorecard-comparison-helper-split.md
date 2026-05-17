# v184 benchmark scorecard comparison helper split

## 本版目标

v184 的目标是把 benchmark scorecard comparison delta builder 里的 relation、normalization、case/group 映射和 explanation 辅助逻辑拆到 `benchmark_scorecard_comparison_helpers.py`。

它解决的问题是：`benchmark_scorecard_comparison_deltas.py` 已经从 comparison entrypoint 中承担 run delta、case delta、group delta、summary、recommendations 和 best-run selection，但底部还混着大量私有 helper。v184 把这些 helper 独立出来，让 deltas 模块回到公共 builder 编排。

本版明确不做：

- 不改变 benchmark scorecard comparison 的 report schema。
- 不改变 JSON/CSV/Markdown/HTML artifact writers。
- 不改变脚本入口、输出文件名和旧 facade 导入。
- 不把 helper 拆分解释成模型能力提升。

## 前置路线

v163 已经把 cross-scorecard comparison 的 delta 与 summary 逻辑从 comparison entrypoint 拆到 `benchmark_scorecard_comparison_deltas.py`。

v182 已经把 Markdown/HTML section rendering 从 artifact writer 拆到 `benchmark_scorecard_comparison_sections.py`。

v184 是对这条 comparison 收口路线的继续推进：entrypoint、artifact、section、delta 都已经分开，delta 内部的比较关系和字段归一化 helper 也应该独立成更清楚的边界。

## 关键文件

### `src/minigpt/benchmark_scorecard_comparison_helpers.py`

这是本版新增的 helper 模块。

它集中处理：

- `_case_delta()`：生成单个 case 的 rubric score delta、missing terms delta、failed checks delta 和 explanation。
- `_case_map()`：把 scorecard 的 `case_scores` 与 rubric cases 合并成以 case name 为 key 的映射。
- `_group_map()`：读取 `drilldowns.task_type` 或 `drilldowns.difficulty`。
- `_run_explanation()`、`_case_explanation()`、`_group_explanation()`：拼装人类可读解释。
- `_score_relation()`、`_flag_relation()`：把数值 delta 转成 improved/regressed/tied/baseline/missing。
- `_delta()`、`_int_delta()`、`_number()`、`_as_int()`：做数值归一化。
- `_list_delta()`、`_string_list()`：计算新增/恢复的 missing terms 和 failed checks。

这些函数仍然是私有 helper，不是新的外部 API。它们服务 comparison delta builder 和后续报告生成。

### `src/minigpt/benchmark_scorecard_comparison_deltas.py`

这个模块保留公共 builder：

- `summarize_benchmark_scorecard_run()`
- `build_benchmark_scorecard_run_delta()`
- `build_benchmark_scorecard_case_deltas()`
- `build_benchmark_scorecard_group_deltas()`
- `build_benchmark_scorecard_summary()`
- `build_benchmark_scorecard_recommendations()`
- `select_best_benchmark_scorecard_run()`

它从 helper 模块导入内部函数，继续维持 `__all__` 中的公共导出不变。

### `tests/test_benchmark_scorecard_comparison_deltas.py`

测试新增 facade identity 检查，确认 `benchmark_scorecard_comparison.py` 旧入口暴露的 run/case/group delta builder 仍然是 deltas 模块中的同一个函数对象。

这保护的是导入契约：旧调用方不需要知道 helper 模块已经被拆出来。

## 数据结构和输入输出

v184 没有改变 comparison report 的结构。

run delta 仍然包含：

- `overall_score_delta`
- `rubric_avg_score_delta`
- `rubric_*_count_delta`
- `generation_quality_total_flags_delta`
- `overall_relation`
- `rubric_relation`
- `generation_quality_flag_relation`
- `explanation`

case delta 仍然包含：

- `case`
- `run_name`
- `baseline_name`
- `rubric_score_delta`
- `relation`
- `added_missing_terms`
- `removed_missing_terms`
- `added_failed_checks`
- `removed_failed_checks`
- `explanation`

这些字段仍然由 comparison artifact writers 和 section renderers 消费。

## 运行流程

拆分后的链路是：

```text
benchmark_scorecard_comparison.py
 -> benchmark_scorecard_comparison_deltas.py
 -> benchmark_scorecard_comparison_helpers.py
 -> comparison report
 -> artifact/section renderers
```

helper 模块只负责纯计算和解释拼装，不负责文件写出、CLI 参数、Markdown/HTML section 结构或截图归档。

## 测试和证据

v184 的截图归档在 `c/184`。

关键验证包括：

- focused benchmark scorecard comparison delta tests。
- helper smoke：确认旧 facade exports 仍然指向 delta builders。
- maintenance smoke：确认维护治理链路仍可跑。
- source encoding hygiene：确认新增/修改 Python 源文件没有 BOM 或语法问题。
- full unittest discovery：确认全仓主测试链路通过。
- docs check：确认 README、`c/184`、代码讲解索引、source/test 关键词对齐。

## 一句话总结

v184 把 benchmark scorecard comparison 的公共 builder 和内部 helper plumbing 分开，让比较链路更清楚，同时保持旧 API、报告 schema 和证据链不变。

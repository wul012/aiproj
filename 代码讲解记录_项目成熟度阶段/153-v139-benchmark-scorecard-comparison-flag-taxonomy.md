# v139 benchmark scorecard comparison flag taxonomy 代码讲解

## 本版目标

v139 的目标是把 v138 已经进入 benchmark scorecard 的 generation-quality flag taxonomy 继续接入跨 scorecard comparison。

v138 让单个 scorecard 能看到：

```text
generation_quality_total_flags
generation_quality_dominant_flag
generation_quality_worst_case
generation_quality_worst_case_status
```

但如果比较两个 run 时只看 overall/rubric/case delta，就会漏掉一种重要情况：分数变化不大，但生成质量问题类型变多了，或者 dominant flag 从 `low_diversity` 变成了 `empty_continuation`。v139 解决的就是这个对齐问题。

本版明确不做：

- 不新增新的模型训练能力。
- 不修改 generation quality 原始分析 schema。
- 不新增 report-only artifact split。
- 不把治理信号描述成模型能力提升。

## 前置路线

本版沿着 v137 -> v138 的链路继续向上消费诊断字段：

```text
v137 generation_quality.summary.flag_summary
 -> v138 benchmark_scorecard.summary generation_quality fields
 -> v139 benchmark_scorecard_comparison run/delta/summary/recommendations
 -> CSV / Markdown / HTML / CLI / c/139 evidence
```

因此 v139 的价值不是“又做了一个报告”，而是让已有 scorecard comparison 在 promotion review 时能解释生成质量弱项是否发生类型漂移。

## 关键文件

- `src/minigpt/benchmark_scorecard_comparison.py`：比较逻辑核心，负责从每个 scorecard summary 中提取 generation-quality taxonomy 字段，并计算相对 baseline 的 delta。
- `src/minigpt/benchmark_scorecard_comparison_artifacts.py`：只读渲染层，负责把 comparison report 写成 CSV、Markdown 和 HTML。
- `scripts/compare_benchmark_scorecards.py`：命令行入口，新增几行关键 summary 输出，方便 smoke 和截图证明链路。
- `tests/test_benchmark_scorecard_comparison.py`：验证真实 build comparison 链路能记录 flag delta、dominant flag change 和 worst case change。
- `tests/test_benchmark_scorecard_comparison_artifacts.py`：验证 artifact module 能把新增字段写入 CSV 和 HTML/Markdown。
- `README.md`、`c/139/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：更新版本说明、证据入口和讲解索引。

## Run Summary 新字段

`_scorecard_run_summary(scorecard, name, index)` 现在从 scorecard summary 中读取：

```python
"generation_quality_total_flags": _as_int(summary.get("generation_quality_total_flags")),
"generation_quality_dominant_flag": summary.get("generation_quality_dominant_flag"),
"generation_quality_worst_case": summary.get("generation_quality_worst_case"),
"generation_quality_worst_case_status": summary.get("generation_quality_worst_case_status"),
```

这些字段的来源是 v138 的 benchmark scorecard summary。comparison 不再回头读取原始 `generation_quality.json`，这样边界更清楚：

```text
generation_quality.py 负责生成原始质量报告
benchmark_scorecard.py 负责把质量报告提升到 run 级 scorecard
benchmark_scorecard_comparison.py 只比较 scorecard 与 scorecard
```

## Delta 语义

`_run_delta(run, baseline)` 新增：

```python
flag_delta = _int_delta(
    run.get("generation_quality_total_flags"),
    baseline.get("generation_quality_total_flags"),
)
```

它进入输出字段：

```text
generation_quality_total_flags_delta
generation_quality_flag_relation
generation_quality_dominant_flag_changed
generation_quality_worst_case_changed
```

这里的 relation 和分数 relation 方向相反。分数越高越好，所以 `+4` 是 improved；flag 越少越好，所以：

```text
flag_delta < 0 -> improved
flag_delta > 0 -> regressed
flag_delta = 0 -> tied
```

因此新增 `_flag_relation()`，避免把 flag delta 错套到 `_score_relation()`。

## Summary 聚合

`_comparison_summary()` 新增几类统计：

```text
baseline_generation_quality_total_flags
baseline_generation_quality_dominant_flag
baseline_generation_quality_worst_case
generation_quality_flag_delta_count
generation_quality_flag_improvement_count
generation_quality_flag_regression_count
generation_quality_dominant_flag_change_count
generation_quality_worst_case_change_count
worst_generation_quality_flag_regression_run
worst_generation_quality_flag_regression_delta
```

这些字段面向的是 review 入口，而不是训练入口。它们回答：

```text
candidate 的 flag 数是否比 baseline 更多？
主导问题类型是否换了？
最差样本是否从一个 case 迁移到另一个 case？
哪一个 compared run 的 flag 增幅最大？
```

## Recommendation 变化

`_recommendations()` 新增三种提示：

```text
Generation-quality flags increased...
Generation-quality flags decreased...
Dominant generation-quality flag changed...
```

这让 comparison 的建议不只盯着 rubric regression。比如某个 run rubric 变化很小，但 flag 从 2 个涨到 8 个，仍然应该在 promotion review 前打开 generation-quality 细节。

## Artifact 展示

`benchmark_scorecard_comparison_artifacts.py` 做了三处展示增强：

- CSV 增加 generation-quality 字段和 delta 字段，便于表格追踪。
- Markdown Summary 增加 flag improvement/regression count 和 baseline dominant flag。
- Markdown/HTML Runs 表增加 `Gen Flags` 和 `Dominant Flag` 列。

artifact 层仍然只消费 report dict，不读取外部 JSON，也不重新计算评分。

## CLI 输出

`scripts/compare_benchmark_scorecards.py` 新增：

```text
generation_quality_flag_regression_count=...
generation_quality_flag_improvement_count=...
baseline_generation_quality_dominant_flag=...
```

这样 `c/139/图片/03-benchmark-scorecard-comparison-taxonomy-smoke.png` 可以直接证明 CLI 层已经看见 taxonomy comparison，而不是只靠打开 JSON。

## 测试覆盖

`tests/test_benchmark_scorecard_comparison.py` 构造 baseline、candidate 和 bad 三个 scorecard：

```text
baseline: flags=4, dominant=low_diversity
candidate: flags=1, dominant=low_diversity
bad: flags=7, dominant=empty_continuation
```

关键断言包括：

```text
generation_quality_flag_improvement_count == 1
generation_quality_flag_regression_count == 1
generation_quality_dominant_flag_change_count == 1
bad generation_quality_total_flags_delta == 3
bad generation_quality_flag_relation == regressed
candidate generation_quality_total_flags_delta == -3
candidate generation_quality_flag_relation == improved
```

`tests/test_benchmark_scorecard_comparison_artifacts.py` 保护 CSV header 和 HTML/Markdown 关键文字，避免 artifact 层以后漏掉新增字段。

## 运行证据

`c/139` 保存五类证据：

- 定向测试、编译检查和 345 个全量 unittest。
- maintenance batching 和 module pressure smoke。
- 临时 baseline/candidate scorecard comparison smoke。
- Playwright/Chrome 渲染 comparison HTML。
- README、归档索引、代码讲解索引和 source encoding hygiene 检查。

这些证据证明本版从核心计算、测试、CLI、artifact 到浏览器渲染都闭环。

## 证据边界

v139 证明的是“跨 scorecard comparison 可以解释 generation-quality flag taxonomy 的变化”。

它不证明 candidate 的模型更好，也不证明训练策略更优。真正的模型能力证据仍然需要真实 checkpoint、固定 prompt suite、多轮训练记录、scorecard comparison 和人工/自动评估共同支撑。

## 一句话总结

v139 把生成质量问题分类从单个 benchmark scorecard 继续推进到跨 run 比较层，让 MiniGPT 的 promotion review 能同时看见分数变化和问题类型漂移。

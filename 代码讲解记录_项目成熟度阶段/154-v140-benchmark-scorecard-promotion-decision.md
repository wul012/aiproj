# v140 benchmark scorecard promotion decision 代码讲解

## 本版目标

v140 的目标是把 v139 的 `benchmark_scorecard_comparison.json` 推进到轻量决策层。

v139 已经能比较：

```text
overall/rubric delta
case regression/improvement
generation_quality_total_flags_delta
dominant flag changed
worst generation case changed
```

但 comparison 仍然是“给人看变化”。v140 新增 `benchmark_scorecard_decision.py`，把这些变化转成候选 run 的 `promote`、`review` 或 `blocked`。

本版明确不做：

- 不重算 benchmark scorecard。
- 不重新分析 generation quality 原始 JSON。
- 不替代 release gate。
- 不把 `promote` 解释成生产级模型质量证明。

## 前置路线

本版沿着最近三版的证据链继续推进：

```text
v137 generation-quality flag taxonomy
 -> v138 scorecard consumes taxonomy
 -> v139 comparison compares taxonomy deltas
 -> v140 decision consumes comparison and selects promotion candidate
```

这让 aiproj 不只是“有报告”，而是能把报告里的弱项信号传到下一步选择逻辑。

## 关键文件

- `src/minigpt/benchmark_scorecard_decision.py`：本版核心模块，读取 comparison，评估候选，写出决策报告。
- `scripts/build_benchmark_scorecard_decision.py`：命令行入口，支持传入 comparison JSON 或 comparison 输出目录。
- `tests/test_benchmark_scorecard_decision.py`：定向测试，覆盖 blocking、promotion、目录加载和 HTML 转义。
- `src/minigpt/__init__.py`：导出 `build_benchmark_scorecard_decision` 和 `write_benchmark_scorecard_decision_outputs`。
- `README.md`、`c/140/解释/说明.md`、`代码讲解记录_项目成熟度阶段/README.md`：版本说明、证据说明和讲解索引。

## 输入格式

`load_benchmark_scorecard_comparison(path)` 支持两种输入：

```text
benchmark_scorecard_comparison.json
包含 benchmark_scorecard_comparison.json 的目录
```

加载后只附加 `_source_path`，不修改原 comparison：

```python
payload["_source_path"] = str(comparison_path)
```

这样 decision 可以追溯来源，同时不破坏 comparison schema。

## 候选评估

核心函数是 `_evaluate_run(run, delta, case_counts, min_rubric_score)`。

它读取 run summary：

```text
overall_score
rubric_avg_score
generation_quality_total_flags
generation_quality_dominant_flag
generation_quality_worst_case
```

同时读取 baseline delta：

```text
overall_score_delta
rubric_avg_score_delta
generation_quality_total_flags_delta
generation_quality_flag_relation
generation_quality_dominant_flag_changed
generation_quality_worst_case_changed
```

再结合 case delta 聚合：

```text
case_regression_count
case_improvement_count
```

## Blockers 与 Review Items

v140 有意区分硬阻断和需要人工复核的项目。

硬阻断 `blockers`：

```text
baseline run is not a promotion candidate
rubric_avg_score is missing
rubric_avg_score below min threshold
rubric score regressed from baseline
overall score regressed from baseline
```

复核项 `review_items`：

```text
rubric fail count increased
generation-quality flags increased
dominant generation-quality flag changed
worst generation-quality case changed
case regression(s)
```

这个分层很重要：分数回退和低于门槛会阻止提升；flag 增加、问题类型变化和 case regression 会提示 review，但不一定直接把所有候选打死。

## 决策关系

每个候选有一个 `decision_relation`：

```text
baseline -> baseline 行，只作参照
blocked  -> 有 blockers
review   -> 无 blockers，但有 review_items
promote  -> 无 blockers，也无 review_items
```

顶层 `decision_status` 来自被选中的候选：

```text
没有可选候选 -> blocked
选中候选有 review_items -> review
选中候选干净 -> promote
```

这让报告能同时表达机器判断和人工复核边界。

## 候选选择

`_select_candidate()` 优先选择：

```text
rubric_avg_score 更高
overall_score 更高
generation_quality_total_flags 更少
name 稳定排序
```

如果存在 clean candidate，优先从 clean candidate 里选；否则从 review candidate 里选。这意味着“可提升”优先于“需要复核”，但项目仍保留 risky candidate 的证据。

## 输出产物

`write_benchmark_scorecard_decision_outputs()` 写出：

```text
benchmark_scorecard_decision.json
benchmark_scorecard_decision.csv
benchmark_scorecard_decision.md
benchmark_scorecard_decision.html
```

JSON 是机器消费入口；CSV 用于表格审查；Markdown/HTML 用于展示和截图。

HTML 的候选表展示：

```text
Run
Relation
Rubric
Overall
Gen Flags
Cases
Blockers
Review Items
```

其中 `Gen Flags` 会显示当前 flag 总数和相对 baseline 的 delta。

## CLI

`scripts/build_benchmark_scorecard_decision.py` 输出：

```text
decision_status=...
recommended_action=...
selected_run={...}
summary={...}
saved_json=...
saved_csv=...
saved_markdown=...
saved_html=...
```

这让 `c/140/图片/03-benchmark-scorecard-decision-smoke.png` 能直接证明决策层已经消费 comparison，而不是只生成文件。

## 测试覆盖

`tests/test_benchmark_scorecard_decision.py` 覆盖：

- candidate 相对 baseline 分数回退时被 blocked。
- baseline 行不会被当成 promotion candidate。
- generation-quality flag 增加会进入 review items。
- clean candidate 会得到 `promote`。
- 目录输入能加载 comparison。
- CSV/Markdown/HTML 输出包含关键字段并做 HTML escaping。
- 空 comparison 会抛出 `ValueError`。

## 运行证据

`c/140` 证明：

- 决策模块定向测试通过。
- 全量 unittest 通过。
- smoke comparison 能生成 decision，并选中 clean candidate。
- Playwright/Chrome 能渲染 decision HTML。
- source encoding hygiene 和文档索引保持干净。

## 证据边界

v140 的 `promote` 只表示“相对 baseline，这个 scorecard 作为 benchmark evidence 可以提升”。

它不表示：

- 模型已经生产可用。
- checkpoint 已经足够强。
- 数据、训练和服务全链路已经满足发布条件。

真正的模型能力提升仍然要靠真实 checkpoint、多轮固定 prompt suite、scorecard comparison、人工复核和训练记录共同证明。

## 一句话总结

v140 把跨 scorecard 的分数变化、case regression 和 generation-quality flag taxonomy 漂移转成轻量 promotion decision，让 aiproj 的 benchmark 治理链从“比较变化”推进到“给出下一步动作”。

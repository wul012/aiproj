# v407 benchmark decision suite design remediation

## 本版目标和边界

v407 的目标是把 v406 已经进入 benchmark scorecard comparison 的 suite-design readiness 继续接入 benchmark scorecard promotion decision。也就是说，决策层不只看 rubric、overall、generation-quality flags、case regression 和 eval-suite comparison readiness，还要判断 prompt suite design 是否适合比较。

本版不训练新 checkpoint，不修改 scorecard 分数计算，也不把 suite-design warning 直接升级为 blocker。它采用更合适的边界：suite-design 不比较就绪时，候选可以保留为 evidence，但不能作为 clean promotion evidence，必须进入 review 并生成专门 remediation。

## 前置能力

本版承接：

- v405：eval suite 报告开始输出 `design_summary`。
- v406：benchmark scorecard 和 scorecard comparison 开始携带 `eval_suite_design_comparison_status`、duplicate seed、expected behavior completeness 等字段。

v407 做的是把这些字段推到决策层，使最终 promote/review/block 判断也能看到“题集设计是否够格”。

## 关键文件

### `src/minigpt/benchmark_scorecard_decision.py`

本版在 `_evaluate_run()` 中读取：

```text
eval_suite_design_coverage_status
eval_suite_design_comparison_status
eval_suite_design_duplicate_seed_count
eval_suite_design_expected_behavior_complete
```

如果 `eval_suite_design_comparison_status` 不是 `pass` 或 `None`，则加入 review item：

```text
suite-design comparison readiness is warn
```

这条 review item 会被 `_categorize_review_items()` 分类为：

```text
suite_design_not_ready
```

它有独立优先级、action 和 remediation metadata：

```text
action_code = make_suite_design_comparison_ready
owner_scope = eval-artifact
target_artifacts = eval_suite, benchmark_scorecard, benchmark_scorecard_comparison
```

summary 新增字段：

- `non_design_comparison_ready_candidate_count`
- `non_design_comparison_ready_candidates`
- `comparison_non_design_comparison_ready_count`
- `comparison_non_design_comparison_ready_runs`
- `comparison_baseline_eval_suite_design_comparison_status`
- `comparison_design_comparison_changed_count`

recommendations 也会明确提示：不能把 selected scorecard 当成 clean model-quality evidence，直到 prompt suite design comparison-ready。

### `src/minigpt/benchmark_scorecard_decision_artifacts.py`

输出层新增 design 字段：

- CSV：增加 `eval_suite_design_coverage_status`、`eval_suite_design_comparison_status`、duplicate seed 和 expected behavior completeness。
- Markdown：summary 增加 non design-ready candidates；candidate table 增加 `Design Compare` 列。
- HTML：顶部 stats 增加 `Design compare review`；candidate table 增加 design compare 列。

这些字段让终端、表格和浏览器都能看到 suite-design review 原因，不需要重新打开 comparison JSON。

### `tests/test_benchmark_scorecard_decision.py`

新增 `test_suite_design_non_ready_candidate_requires_review_without_blocking()`：

- 构造 clean candidate：rubric、overall、generation flags 都符合 promote 条件。
- 只把 `candidate_design_status` 设置成 `warn`。
- 断言最终 decision 是 `review`，不是 `promote`。
- 断言 selected run 带有 `suite-design comparison readiness is warn`。
- 断言 summary、recommendations 和 remediation plan 都使用 `suite_design_not_ready`。

同时更新输出测试，确保 CSV、Markdown 和 HTML 都能看到 design comparison 字段。

## 输入输出

输入仍是 `benchmark_scorecard_comparison.json` 或其目录。

输出增加：

```text
benchmark_scorecard_decision.json
  selected_run.eval_suite_design_comparison_status
  summary.non_design_comparison_ready_candidate_count
  remediation_plan[].category = suite_design_not_ready

benchmark_scorecard_decision.csv
  eval_suite_design_comparison_status

benchmark_scorecard_decision.md/html
  Design Compare
  Design compare review
```

这些产物是决策证据，不是模型能力证明。

## 测试覆盖

定向验证命令：

```text
python -m pytest tests\test_benchmark_scorecard_decision.py tests\test_benchmark_scorecard_comparison_deltas.py tests\test_benchmark_scorecard_comparison_artifacts.py tests\test_benchmark_scorecard.py -q
```

该验证覆盖 v407 新增 decision 层，同时回归 v406 的 scorecard 和 comparison 字段传递。

## 一句话总结

v407 把 prompt suite 设计不就绪从 scorecard caveat 推进成 promotion decision 的正式 review/remediation 条件，防止题集设计问题被最终决策层漏掉。

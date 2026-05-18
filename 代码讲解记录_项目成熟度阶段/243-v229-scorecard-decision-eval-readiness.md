# v229 scorecard decision eval readiness 代码讲解

## 本版目标

v229 的目标是把 eval-suite comparison readiness 从 scorecard comparison 继续带到 benchmark scorecard promotion decision。

v226 让 eval suite 产生 readiness，v227 让 scorecard 消费 readiness，v228 让 comparison 保留 readiness。v229 解决最后一层：候选 promotion 决策不能忽略这份 readiness。

## 不做什么

本版不改变 regression blocker 规则。

本版不把 non-comparison-ready 直接设为 blocker。

本版也不改变 scorecard decision 的 schema version，只增加兼容字段。

## `src/minigpt/benchmark_scorecard_decision.py`

### `_evaluate_run()`

candidate evaluation 现在会读取：

```text
eval_suite_coverage_status
eval_suite_comparison_status
```

如果 `eval_suite_comparison_status` 不是 `pass` 且不是缺失值，就加入 review item：

```text
eval-suite comparison readiness is warn
```

这样 clean candidate 会从 `promote` 变成 `review`，但不会变成 `blocked`。

这个选择是有意的：non-comparison-ready 代表评估证据不干净，不一定代表 candidate 本身更差。

### `_summary()`

summary 新增：

```text
non_comparison_ready_candidate_count
non_comparison_ready_candidates
comparison_non_comparison_ready_count
comparison_non_comparison_ready_runs
comparison_baseline_eval_suite_comparison_status
```

这些字段把 v228 comparison 里的 readiness 上下文带进最终 decision。

### `_recommendations()`

如果 selected run 不是 comparison-ready，recommendations 会提示：

```text
Do not treat the selected scorecard as clean model-quality evidence until its eval suite is comparison-ready.
```

如果 comparison summary 里已经标出 non-comparison-ready runs，也会提示这些 runs 名称。

如果 baseline 不是 comparison-ready，则提示先换成更干净的 baseline。

## `src/minigpt/benchmark_scorecard_decision_artifacts.py`

CSV 输出新增：

```text
eval_suite_coverage_status
eval_suite_comparison_status
```

Markdown 的 candidate table 新增 `Eval Compare` 列。

HTML 的 stats 新增 `Eval compare review`，candidate table 也新增 eval compare 列。

这保证 JSON、CSV、Markdown、HTML 四种产物都能看到 readiness 进入了 promotion decision。

## `tests/test_benchmark_scorecard_decision.py`

测试 fixture `make_comparison()` 新增：

```text
candidate_eval_status
```

新增测试：

```text
test_eval_suite_non_ready_candidate_requires_review_without_blocking
```

它构造一个本来可以 promote 的 clean candidate，但把：

```text
eval_suite_comparison_status = warn
```

然后断言：

- `decision_status == review`
- selected run 仍是 candidate。
- review items 包含 `eval-suite comparison readiness is warn`。
- summary 记录 non-comparison-ready candidate。
- recommendations 提醒不要把 selected scorecard 当成 clean model-quality evidence。

原有 promote 测试仍证明 `pass` readiness 不会影响 clean candidate 晋级。

## 输入输出

输入仍然是 `benchmark_scorecard_comparison.json`。

新消费字段来自 comparison 的 runs 和 summary：

```text
runs[].eval_suite_coverage_status
runs[].eval_suite_comparison_status
summary.non_comparison_ready_runs
summary.baseline_eval_suite_comparison_status
```

输出是 decision JSON/CSV/Markdown/HTML 的增量字段和推荐语。

## 运行证据

本版运行证据归档在 `c/229`：

- `图片/01-scorecard-decision-readiness-tests.png`
- `图片/02-scorecard-decision-readiness-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v229 让 benchmark scorecard promotion decision 不再只依赖分数和 regression 关系。

它把“评估是否可比”放入候选选择的 review 语义中，避免把不干净的 eval 证据误当作模型质量提升。

## 一句话总结

v229 把 eval-suite 可比性推进到 benchmark promotion decision，让 selected scorecard 的晋级状态带上更真实的评估证据边界。

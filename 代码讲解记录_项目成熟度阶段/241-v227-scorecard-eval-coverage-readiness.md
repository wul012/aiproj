# v227 scorecard eval coverage readiness 代码讲解

## 本版目标

v227 的目标是把 v226 新增的 eval-suite coverage readiness 接到 benchmark scorecard。

v226 已经让 `eval_suite.json` 自己能说明：

```text
status
comparison_status
blockers
comparison_blockers
```

但如果 benchmark scorecard 仍然只按 `case_count * 20` 计算 eval coverage，那么 5 个 case 的小型 suite 仍可能拿到满分。v227 解决的就是这个下游消费缺口。

## 不做什么

本版不改变 eval suite 的生成方式。

本版不改变 benchmark scorecard 的 schema version。

本版不删除旧 case-count 评分逻辑。历史 `eval_suite.json` 没有 `coverage` 字段时，仍保持旧行为，避免老 run 的 scorecard 生成被突然降分。

## `src/minigpt/benchmark_scorecard.py`

### `_eval_coverage_component()`

原逻辑只读取：

```python
case_count = _number(_pick(eval_suite, "case_count")) or 0
score = min(100.0, case_count * 20.0)
```

v227 保留这个基础分，但增加 coverage readiness 约束：

```python
coverage = _eval_suite_coverage(eval_suite)
```

如果 `coverage.status != "pass"`，eval coverage score 最多只能到 `55.0`。

如果 `coverage.status == "pass"` 但 `coverage.comparison_status != "pass"`，score 最多只能到 `75.0`。

这表示：

- suite 不具备基础代表性时，不应作为 pass 证据。
- suite 有基础代表性但不适合 checkpoint comparison 时，只能作为 warning-level 证据。
- 历史 artifact 没有 coverage 时，继续用旧 case-count 分。

### `_eval_suite_coverage()`

这个 helper 支持两个读取位置：

```text
eval_suite["coverage"]
eval_suite["benchmark"]["coverage"]
```

原因是 v226 同时写了顶层和 `benchmark` 内部字段，方便不同消费者读取。scorecard 作为下游消费者，要同时兼容这两个位置。

### `_eval_coverage_metrics()`

scorecard component 的 `metrics` 现在会保留：

```text
coverage_available
coverage_status
comparison_status
decision
comparison_decision
task_type_count
difficulty_count
tag_count
blockers
comparison_blockers
```

这些字段不是展示装饰，而是后续 scorecard comparison、promotion decision 或 maturity narrative 可以继续消费的机器可读证据。

### `_score_summary()`

summary 新增：

```text
eval_suite_coverage_status
eval_suite_comparison_status
```

这样报告的最上层 summary 就能直接看到 eval suite 是否可比，不需要每次深入 components。

### `_recommendations()`

如果 eval coverage component 的 `comparison_status` 不是 `pass`，recommendations 会提示：

```text
Prefer `builtin:standard-zh` or another comparison-ready suite before claiming checkpoint quality gains.
```

如果存在 `comparison_blockers`，也会把 blockers 拼进推荐语。这样人读报告时不会只看到总分，还能看到为什么这份 eval 证据不足以支撑 checkpoint improvement 说法。

## `tests/test_benchmark_scorecard.py`

本版增加一个 focused test：

```text
test_eval_coverage_component_uses_eval_suite_readiness_when_available
```

测试构造一个旧 run，然后给 `eval_suite.json` 注入 v226 风格的 coverage：

```json
{
  "status": "pass",
  "comparison_status": "warn",
  "comparison_blockers": ["missing comparison difficulties: hard"]
}
```

断言包括：

- `eval_coverage.status == "warn"`
- `eval_coverage.score == 75.0`
- component metrics 里保留 `coverage_status` 和 `comparison_status`
- summary 里暴露 eval suite coverage/comparison status
- recommendations 提示使用 comparison-ready suite
- recommendations 透出 `missing comparison difficulties: hard`

原有主测试也增加了两个兼容断言：

```text
eval_suite_coverage_status is None
eval_suite_comparison_status is None
```

这证明历史 eval artifact 没有 coverage 时，不会被错误填充状态或改变旧评分逻辑。

## 输入输出

输入仍然是 run 目录下的：

```text
eval_suite/eval_suite.json
generation-quality/generation_quality.json
pair_batch/pair_generation_batch.json
```

新增消费的是 `eval_suite.json` 中可选的：

```text
coverage
benchmark.coverage
```

输出仍然是 benchmark scorecard JSON/CSV/Markdown/HTML，但 eval coverage component 和 summary 会多带 readiness 信息。

## 运行证据

本版运行证据归档在 `c/227`：

- `图片/01-scorecard-readiness-tests.png`
- `图片/02-scorecard-readiness-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

这些截图分别证明：聚焦测试通过、readiness 降分 smoke 可见、source encoding 干净、全量测试通过。

## 证据链角色

v227 不新增模型能力，但它让模型评估证据链更诚实。

v226 负责让 eval suite 自己说清楚“我是否适合对比”。v227 负责让 benchmark scorecard 真正消费这个判断，不再只按 case 数给 eval coverage 满分。

这让后续 scorecard promotion、training scale decision 和 maturity narrative 有机会基于 comparison readiness 做更稳的模型质量判断。

## 一句话总结

v227 把 eval-suite readiness 从单独报告推进到 benchmark scorecard 总评，让 checkpoint 质量对比不再只依赖 prompt 数量。

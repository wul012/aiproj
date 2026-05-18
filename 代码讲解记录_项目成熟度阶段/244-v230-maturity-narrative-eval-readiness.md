# v230 maturity narrative eval readiness 代码讲解

## 本版目标

v230 的目标是把 benchmark scorecard promotion decision 里的 eval-suite comparison readiness 继续带到 maturity narrative。

v226 到 v229 已经让 readiness 从 eval suite 进入 scorecard、comparison 和 promotion decision。v230 解决的是最后的项目级表达：组合成熟度叙事不能只说“有 promotion decision”，还要说明这个 decision 是否带着 non-comparison-ready 的评估边界。

## 不做什么

本版不改变 scorecard decision 本身的 promote/review/blocker 规则。

本版不新增新的报告类型，也不改变 maturity narrative 的输入发现规则。

本版只把既有 decision 证据向 summary、section、Markdown 和 HTML 继续传播。

## `src/minigpt/maturity_narrative_summary.py`

### `build_maturity_narrative_summary()`

summary 新增四类字段：

```text
benchmark_decision_selected_eval_suite_comparison_status
benchmark_decision_non_comparison_ready_candidate_count
benchmark_decision_non_comparison_ready_candidates
benchmark_decision_eval_suite_comparison_status_counts
```

这些字段来自 `benchmark_scorecard_decision.json` 的 summary、selected run 和 candidate evaluations。

如果上游 decision 已经写入 `non_comparison_ready_candidates`，本版优先使用该字段；如果旧产物没有这个字段，则从 candidate evaluations 中按 `eval_suite_comparison_status != pass` 回推候选名。

### `_portfolio_status()`

portfolio status 现在会读取 scorecard decision 行：

```text
decision_status in {review, blocked}
non_comparison_ready_candidate_count > 0
```

满足任一条件时，maturity narrative 进入 `review`。

这不是说模型一定变差，而是说明组合叙事不能把这份 promotion decision 当成 clean model-quality evidence。

### `build_maturity_narrative_recommendations()`

当存在 non-comparison-ready candidate 时，recommendations 先给出专门提示：

```text
Treat scorecard promotion as review-only until non-comparison-ready eval suites are rerun with comparable benchmark evidence.
```

这条建议比通用 review 建议更具体，指出问题在 eval 可比性，而不是泛泛地说“需要人工审查”。

## `src/minigpt/maturity_narrative_sections.py`

Benchmark Promotion Decision section 现在使用 `_benchmark_decision_status()`。

如果 non-comparison-ready candidate count 大于 0，section status 直接显示 `warn`。

section claim 会写出：

```text
selected eval comparison status
candidate(s) are not comparison-ready
```

section boundary 也明确说明：promotion decision 不是生产发布批准；当 eval suites 不可比时，也不是 clean model-quality claim。

## `src/minigpt/maturity_narrative_artifacts.py`

Markdown Portfolio Summary 新增：

```text
Scorecard decision eval compare
Scorecard decision non-ready candidates
```

HTML stats 新增：

```text
Decision eval
Decision non-ready
```

这样 maturity narrative 的人读版本和网页版本都能直接看到 eval readiness 边界，不需要再翻到下游 JSON 才知道为什么组合状态进入 review。

## `tests/test_maturity_narrative.py`

测试 fixture 里的 scorecard decision 增加 pass 状态，保护原本 ready portfolio 不被误伤。

新增测试：

```text
test_build_maturity_narrative_marks_review_for_non_comparison_ready_decision
```

它把 decision 改成：

```text
decision_status = review
selected eval_suite_comparison_status = warn
non_comparison_ready_candidates = ["demo-run"]
```

然后断言：

- portfolio status 变为 `review`。
- selected eval comparison status 被写入 summary。
- non-ready candidate count 和 names 被保留。
- Benchmark Promotion Decision section 变为 `warn`。
- recommendations 包含 `review-only` 提示。

输出测试还断言 Markdown/HTML 暴露了新增字段。

## 输入输出

输入仍然是 maturity narrative 原有输入：

```text
maturity_summary.json
registry.json
request_history_summary.json
benchmark_scorecard.json
benchmark_scorecard_decision.json
dataset_card.json
```

本版主要消费 `benchmark_scorecard_decision.json` 中的：

```text
summary.non_comparison_ready_candidate_count
summary.non_comparison_ready_candidates
selected_run.eval_suite_comparison_status
candidate_evaluations[].eval_suite_comparison_status
```

输出仍然是 maturity narrative JSON/Markdown/HTML，只是 summary、section claim 和渲染表格多了 eval readiness 字段。

## 运行证据

本版运行证据归档在 `c/230`：

- `图片/01-maturity-narrative-readiness-tests.png`
- `图片/02-maturity-narrative-readiness-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v230 把“eval 是否可比”从 promotion decision 推到成熟度叙事入口。

这让项目级总结不再只看有没有 decision，而是能表达 decision 是否适合作为 clean portfolio evidence。

## 一句话总结

v230 让 maturity narrative 识别 scorecard decision 的 eval 可比性边界，把不干净的 promotion evidence 明确降级为组合层面的 review 信号。

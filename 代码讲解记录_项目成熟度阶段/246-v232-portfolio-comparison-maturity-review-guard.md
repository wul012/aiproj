# v232 portfolio comparison maturity review guard 代码讲解

## 本版目标

v232 的目标是让 training portfolio comparison 在选择 best score 时不要忽略 maturity narrative 的 review 状态。

v230-v231 已经把 eval readiness 推到 maturity narrative，并用链路测试保护。v232 继续往训练组合比较层收束：如果一个组合分数最高，但 maturity narrative 是 `review`，它不能被描述成 clean baseline。

## 不做什么

本版不改变训练、评估或 scorecard 计算。

本版不新增新的报告层。

本版不阻断 best-score 选择，只让 summary 和 recommendations 明确 review 边界。

## `src/minigpt/training_portfolio_comparison.py`

### `_comparison_summary()`

summary 原来已经统计：

```text
maturity_review_count
best_score_name
```

但它没有把 best-score 组合自己的 maturity 状态写出来。v232 新增：

```text
best_score_maturity_status
```

实现方式是先计算一次 best-score、best-artifact 和 lowest-val-loss：

```text
best_score = _best_numeric(portfolios, "overall_score", higher_is_better=True)
```

再从 best-score portfolio 上读取：

```text
maturity_portfolio_status
```

这样 summary 能表达两个事实：

- 哪个组合分数最高。
- 这个最高分组合是否仍处于 maturity review。

### `_recommendations()`

当 `maturity_review_count > 0` 时，recommendations 新增提示：

```text
Review maturity narrative status before promoting the best-scoring portfolio as a clean baseline.
```

这条提示不改变排序结果，但会阻止读者把高分组合自动理解成可作为 clean baseline 的模型质量提升。

## `tests/test_training_portfolio_comparison.py`

原有比较测试增加断言：

```text
best_score_name = candidate
best_score_maturity_status = ready
```

新增测试：

```text
test_best_scoring_review_portfolio_keeps_maturity_warning
```

它构造：

```text
baseline: score 82, maturity ready
candidate: score 91, maturity review
```

然后断言：

- best score 仍然是 `candidate`。
- `best_score_maturity_status == review`。
- `maturity_review_count == 1`。
- recommendations 中包含 maturity narrative status 提示。

这个测试保护的是语义边界：高分可以被选中，但不应被误读为 clean evidence。

## 输入输出

输入仍然是 training portfolio comparison 的原有 portfolio JSON。

每个 portfolio 通过 `artifacts.maturity_narrative` 读取：

```text
summary.portfolio_status
```

输出新增 summary 字段：

```text
best_score_maturity_status
```

同时 recommendations 多一条 maturity review 提醒。

## 运行证据

本版运行证据归档在 `c/232`：

- `图片/01-training-portfolio-comparison-tests.png`
- `图片/02-portfolio-maturity-review-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v232 把 maturity narrative 的 review 语义继续带到 training portfolio comparison。

它让“最佳分数”和“是否可作为 clean baseline”分开表达，避免把治理风险藏在高分后面。

## 一句话总结

v232 让 training portfolio comparison 在推荐高分组合前保留 maturity review 边界，使训练组合比较更诚实、更适合作为后续 baseline 依据。

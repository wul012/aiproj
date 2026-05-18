# v234 portfolio maturity recommendation precision 代码讲解

## 本版目标

v234 的目标是收窄 training portfolio comparison 的 maturity recommendation 语义。

v232-v233 已经让 best-score maturity status 进入 summary 和人读输出。v234 进一步区分两种情况：

- 最高分 portfolio 自己是 review。
- 其它非领先 portfolio 是 review，但最高分 portfolio 是 ready。

这两种情况不应该给同一句提示。

## 不做什么

本版不改变 best-score 选择。

本版不改变 maturity review count 的统计。

本版不新增报告层，只调整 recommendations 文案和测试。

## `src/minigpt/training_portfolio_comparison.py`

### `_recommendations()`

旧逻辑是：

```text
if maturity_review_count:
    Review maturity narrative status before promoting the best-scoring portfolio as a clean baseline.
```

这个提示在“review 来自非领先组合”时过宽，因为它会暗示 best-scoring portfolio 本身也不干净。

新逻辑先看：

```text
summary.best_score_maturity_status
```

如果最高分 portfolio 的 maturity 状态是：

```text
review / warn / fail / incomplete
```

则提示：

```text
Review the best-scoring portfolio's maturity narrative before promoting it as a clean baseline.
```

如果 maturity review 只出现在非领先组合，则提示：

```text
Review maturity-narrative findings for non-leading portfolios before archiving the comparison.
```

这样 reviewer 能知道问题在哪里，不会把所有 review 都误归因到最高分组合。

## `tests/test_training_portfolio_comparison.py`

原有 comparison 测试中，最高分 candidate 是 ready，另一个 review 组合分数更低。现在断言 recommendations 包含：

```text
non-leading portfolios
```

新增的 best-score review 测试继续断言：

```text
best-scoring portfolio's maturity narrative
```

两个分支都被覆盖：

- best-score ready + non-leading review。
- best-score review。

## 输入输出

输入不变，仍然来自 training portfolio comparison summary：

```text
maturity_review_count
best_score_maturity_status
```

输出只改变 recommendations 文案。

## 运行证据

本版运行证据归档在 `c/234`：

- `图片/01-training-portfolio-recommendation-tests.png`
- `图片/02-portfolio-recommendation-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v234 是一个语义精修版。

它让 recommendation 不只“保守”，还更准确地指向风险来源。

## 一句话总结

v234 让 training portfolio comparison 的 maturity review 提醒从泛化警告变成定向建议，减少高分 ready 组合被 review 文案误伤的风险。

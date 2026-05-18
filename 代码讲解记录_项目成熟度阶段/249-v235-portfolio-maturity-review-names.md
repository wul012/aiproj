# v235 portfolio maturity review names 代码讲解

## 本版目标

v235 的目标是让 training portfolio comparison 不只统计 maturity review 数量，还能说清楚是哪几个 portfolio 处于 review。

v232-v234 已经把 maturity review 边界推进到 best-score summary、Markdown/HTML 和 recommendations。v235 解决可追踪性：review count 如果没有名字，人工排查仍要翻 portfolio 表格。

## 不做什么

本版不改变比较排序。

本版不改变 recommendations 分支。

本版只增加 review 名单字段和展示。

## `src/minigpt/training_portfolio_comparison.py`

### `_comparison_summary()`

新增中间变量：

```text
maturity_review_rows
```

它筛选：

```text
maturity_portfolio_status in {"review", "warn", "fail", "incomplete"}
```

summary 现在新增：

```text
maturity_review_names
```

字段值是进入 review 的 portfolio 名称列表。

原来的：

```text
maturity_review_count
```

改为直接使用 `len(maturity_review_rows)`，避免 count 和 names 分别计算造成不一致。

## `src/minigpt/training_portfolio_comparison_artifacts.py`

### Markdown Summary

Summary 表新增：

```text
Maturity review portfolios
```

如果没有 review portfolio，就显示：

```text
none
```

### HTML Stats

stats cards 新增：

```text
Maturity reviews
```

值为 review portfolio 名称列表，或者 `none`。

这让 HTML 顶部总览也能直接定位 review 来源。

## `tests/test_training_portfolio_comparison.py`

测试覆盖两种场景：

- 最高分 candidate 是 ready，低分 review portfolio 名为 `review`。
- 最高分 candidate 自己是 review。

分别断言：

```text
maturity_review_names == ["review"]
maturity_review_names == ["candidate"]
```

输出测试还断言 Markdown/HTML 暴露 review portfolio 名称区域。

## `tests/test_training_portfolio_comparison_artifacts.py`

artifact fixture summary 增加：

```text
maturity_review_names = ["candidate"]
```

并断言 Markdown/HTML 输出含有相应标题。

## 输入输出

输入不变，仍来自每个 portfolio 链接的：

```text
maturity_narrative.summary.portfolio_status
```

输出新增：

```text
summary.maturity_review_names
```

并在 Markdown/HTML 人读输出中展示。

## 运行证据

本版运行证据归档在 `c/235`：

- `图片/01-training-portfolio-review-name-tests.png`
- `图片/02-portfolio-review-name-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v235 不是扩大治理链，而是让已有 review 证据更容易追踪。

它把“有 review”变成“谁在 review”，减少人工翻查成本。

## 一句话总结

v235 为 training portfolio comparison 增加 maturity review 名单，让 portfolio-level 治理风险从计数升级为可定位证据。

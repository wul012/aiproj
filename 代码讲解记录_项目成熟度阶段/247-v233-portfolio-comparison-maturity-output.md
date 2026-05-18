# v233 portfolio comparison maturity output 代码讲解

## 本版目标

v233 的目标是把 v232 新增的 best-score maturity status 暴露到人读报告里。

v232 已经让 JSON summary 和 recommendations 知道：最高分 portfolio 如果 maturity narrative 是 `review`，不能直接当 clean baseline。v233 解决的是展示层问题：如果 Markdown 和 HTML 总览看不到这个字段，人工 review 仍然容易漏掉边界。

## 不做什么

本版不改变 training portfolio comparison 的计算逻辑。

本版不新增字段来源，也不改变 JSON schema 语义。

本版只补 Markdown/HTML 输出和对应测试。

## `src/minigpt/training_portfolio_comparison_artifacts.py`

### Markdown Summary

`render_training_portfolio_comparison_markdown()` 的 Summary 表新增：

```text
Best score maturity
```

它读取：

```text
summary.best_score_maturity_status
```

这样打开 `training_portfolio_comparison.md` 时，读者能在总览区域同时看到：

- best score 是谁。
- best score 的 maturity 状态是否为 review。

### HTML Stats

`render_training_portfolio_comparison_html()` 的 stats cards 新增：

```text
Best score maturity
```

这个位置比 portfolio 表格更醒目，适合演示和快速扫描。

## `tests/test_training_portfolio_comparison.py`

原有输出测试增加断言：

```text
Best score maturity
```

同时检查 Markdown 和 HTML。

这保护真实 builder 输出路径，避免后续 JSON 有字段但 artifact 渲染忘记展示。

## `tests/test_training_portfolio_comparison_artifacts.py`

artifact split 测试的 fixture summary 增加：

```text
best_score_maturity_status = review
```

然后断言 Markdown 和 HTML 都包含 `Best score maturity`。

这保护 artifact writer 本身，和 builder 测试形成双层覆盖。

## 输入输出

输入仍然是 training portfolio comparison report。

本版读取已有字段：

```text
summary.best_score_maturity_status
```

输出变化：

- Markdown Summary 多一行。
- HTML stats 多一卡。

## 运行证据

本版运行证据归档在 `c/233`：

- `图片/01-training-portfolio-output-tests.png`
- `图片/02-portfolio-maturity-output-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v233 没有改变判断规则，而是让 v232 的判断更容易被人看到。

它避免出现“机器 JSON 里有 review 边界，人工 HTML 页面却只看到 best score”的断层。

## 一句话总结

v233 把 best-score maturity status 从机器可读 summary 推到 Markdown/HTML 总览，让训练组合比较的人读报告也能保留 review 边界。

# 316. v302 training portfolio batch CI regression summary

## 本版目标与边界

v302 的目标是把 v301 training portfolio comparison 里的 CI regression review summary 继续传入 training portfolio batch。v301 已经能在单个 comparison 报告中把 `ci-regressed` best-score portfolio 变成 blocker action；但 batch 总览仍主要显示 review/blocker 数量和 coverage-regressed portfolio，CI-regressed portfolio 名称需要打开嵌套 comparison JSON 才能看到。

所以这一版补的是 batch 层可见性：让 batch Markdown、HTML 和 CLI stdout 都直接显示 CI-regressed portfolio，避免批量训练组合的入口报告漏掉 CI governance 风险。

本版不改变训练执行、比较算法、maturity narrative 判定或 blocker 规则。它只消费 v301 已经产生的 comparison review summary 字段。

## 前置链路

这版承接 v300-v301：

- v300：maturity narrative 将 CI workflow/order regression 表达为 `review` 信号。
- v301：training portfolio comparison 将 CI regression 表达为 blocker/review action。
- v302：training portfolio batch 将 nested comparison 的 CI regression summary 提升到 batch 总览和 CLI。

v302 的位置更靠近 batch workflow 入口。它不发明新治理规则，只减少 reviewer 在多个 nested artifact 之间查找的成本。

## 关键文件

- `src/minigpt/training_portfolio_batch.py`
  - `_comparison_review_summary()` 现在读取：
    - `maturity_ci_regression_count`
    - `maturity_ci_regression_names`
  - 这些字段来自 nested `training_portfolio_comparison` 的 `summary`。
  - `comparison_review_summary` 继续保留 blocker reasons 和 blocker portfolios，因此 `best_score_ci_regressed` 可以在 batch 层被直接看到。

- `src/minigpt/training_portfolio_batch_artifacts.py`
  - Markdown 顶部 summary 增加 `CI-regressed portfolios`。
  - Markdown Comparison 表格增加 `CI regressions`。
  - HTML stats 增加 CI regression count。
  - HTML Comparison Hook 增加 CI regression portfolio names。
  - Coverage regression 字段仍保留，不改变原有 coverage review 语义。

- `scripts/run_training_portfolio_batch.py`
  - CLI stdout 增加 `comparison_review_summary=...`。
  - 这样命令行日志和 CI smoke 不必打开 JSON 文件，也能看到 review/blocker/CI regression 汇总。

- `tests/test_training_portfolio_batch.py`
  - `_comparison_review_summary()` 测试增加 CI regression count/name。
  - blocker reason 改为 `best_score_ci_regressed`，验证 v301 新 blocker 能被 batch 层保留。
  - renderer 测试确认 Markdown/HTML 都显示 CI regression 字段。

## 核心字段语义

本版在 batch 层新增消费：

```text
comparison_review_summary.maturity_ci_regression_count
comparison_review_summary.maturity_ci_regression_names
```

它们来自 comparison summary：

```text
training_portfolio_comparison.summary.maturity_ci_regression_count
training_portfolio_comparison.summary.maturity_ci_regression_names
```

这些字段表示 portfolio comparison 中有 maturity narrative CI regression。它不表示模型分数下降，也不替代 coverage regression、dataset warning、artifact coverage 或 validation loss delta。

## 运行流程

典型链路如下：

```text
maturity_narrative
  -> training_portfolio_comparison
  -> comparison_review_summary
  -> training_portfolio_batch Markdown / HTML / CLI
```

如果 nested comparison 输出：

```text
maturity_ci_regression_count=1
maturity_ci_regression_names=["candidate"]
review_actions=[reason=best_score_ci_regressed]
```

则 batch 层会显示：

```text
CI-regressed portfolios: candidate
CI regressions: candidate
Blocker reasons: best_score_ci_regressed
```

这让 batch 报告成为更完整的审查入口。

## 测试覆盖

本版测试聚焦 batch 消费边界：

- `_comparison_review_summary()` 保留 CI regression 数量和 portfolio 名称。
- blocker reason 保留 `best_score_ci_regressed`。
- Markdown 渲染包含 `CI-regressed portfolios`。
- HTML 渲染包含 `CI regressions`。
- 邻近 comparison 测试和 batch 测试一起运行，确认 v301 到 v302 的字段传递没有断层。

## 文档与归档

README 当前版本、latest checkpoint、tag 列表、`c/README.md` 和代码讲解索引都更新到 v302。

运行截图和解释归档在 `c/302`：

- `c/302/图片/01-training-portfolio-batch-tests.png`
- `c/302/图片/02-py-compile.png`
- `c/302/图片/03-full-unittest.png`
- `c/302/图片/04-source-encoding.png`
- `c/302/图片/05-coverage-gate.png`
- `c/302/图片/06-docs-code-check.png`

`c/302/解释/说明.md` 说明每张截图证明什么。

## 链路角色

v302 是 CI regression review 的 batch 可见性版本。它让 batch 总览直接承接 comparison blocker 语义，而不是让 reviewer 在 batch 报告、comparison JSON 和 maturity narrative 之间反复跳转。

一句话总结：v302 把 training portfolio comparison 的 CI regression 风险提升到 batch 入口，让批量训练组合也能直接看见哪个 portfolio 因 CI governance 回归需要拦截。

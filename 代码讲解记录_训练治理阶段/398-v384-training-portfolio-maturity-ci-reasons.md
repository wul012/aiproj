# v384 training portfolio maturity CI reasons 代码讲解

## 本版目标和边界

v384 的目标是把 v383 maturity narrative 已经具备的 release readiness CI workflow regression reasons 带入 training portfolio comparison。

v383 让成熟度叙事能说明 CI 回归原因，但 portfolio comparison 仍只看到 `ci_workflow_regression_count` 和 `ci_workflow_order_regression_count`。这会导致训练组合比较层能判断“这个候选有 CI 回归”，却不能直接解释“为什么回归”。v384 补齐这个缺口：portfolio summary、comparison summary、review action、recommendation、CSV、Markdown 和 HTML 都能看到 reason counts。

本版不新增新的报告类型，不改变 maturity narrative 的判断算法，不改变 portfolio comparison 的 best-score 选择规则，也不改变 CLI 参数。它只沿用已有 maturity narrative -> training portfolio comparison 链路做原因透传。

## 前置能力

本版承接 v381-v383：

```text
release_readiness_comparison.summary.ci_workflow_regression_reason_counts
        |
        v
registry.release_readiness_delta_summary.ci_workflow_regression_reason_counts
        |
        v
maturity summary / maturity narrative
        |
        v
training portfolio comparison / review actions / rendered outputs
```

这条链路的意义是：底层 release readiness comparison 负责发现 CI 回归原因，registry 和 maturity 负责聚合与解释，training portfolio comparison 负责在训练组合选择时把原因放到 promotion review 面前。

## 关键文件

### `src/minigpt/training_portfolio_comparison.py`

`_portfolio_summary()` 现在从 linked `maturity_narrative.json` 的 `summary` 中读取：

```text
release_readiness_ci_workflow_regression_reasons
release_readiness_ci_workflow_regression_reason_counts
```

并提升为 portfolio 层字段：

```text
maturity_release_readiness_ci_workflow_regression_reasons
maturity_release_readiness_ci_workflow_regression_reason_counts
```

如果旧 artifact 只有 reasons 列表而没有 counts，代码会用 `_count_strings()` 从列表回退计算；如果两个字段都没有，则保持空列表和空映射，不伪造原因。

`_comparison_summary()` 新增：

```text
maturity_ci_regression_reason_counts
best_score_maturity_release_readiness_ci_workflow_regression_reasons
best_score_maturity_release_readiness_ci_workflow_regression_reason_counts
```

`maturity_ci_regression_reason_counts` 由 `_merge_reason_counts()` 聚合所有 CI-regressed portfolio 的原因计数。best-score 字段用于判断“当前最优分数候选是否也带着 CI 原因阻断”。

`_delta_explanation()` 在发现 maturity CI regression 时，会把原因计数追加到解释文本，例如：

```text
release-readiness CI regressed (ci_failed_checks_increased:1)
```

这个解释属于人读辅助，不是新的机器判定源。机器判定仍使用结构化 count 字段。

### `src/minigpt/training_portfolio_comparison_review.py`

`build_training_portfolio_recommendations()` 会读取 summary 级别的 `maturity_ci_regression_reason_counts`，让建议不只说“CI workflow regressions”，而是直接带上原因：

```text
Block best-score promotion until release-readiness CI workflow regressions are explained or fixed (ci_failed_checks_increased:1).
```

`build_training_portfolio_review_actions()` 在 CI regression action 的 evidence 中新增：

```text
ci_workflow_regression_reasons
ci_workflow_regression_reason_counts
```

这让 blocker/review action 的证据可以被后续门禁、人工审阅或归档工具复用，而不是只藏在 action 文本里。

### `src/minigpt/training_portfolio_comparison_artifacts.py`

CSV 新增两列：

```text
maturity_release_readiness_ci_workflow_regression_reasons
maturity_release_readiness_ci_workflow_regression_reason_counts
```

Markdown summary 新增：

```text
Maturity CI regression reasons
```

Portfolio 表里的 maturity 单元格新增 `ci_reasons=...`，HTML stat cards 也展示 `CI regression reasons`。这些渲染产物是最终人读证据；下游如果要做机器消费，应读取 JSON。

### `tests/test_training_portfolio_comparison.py`

测试 fixture `make_portfolio()` 支持写入 CI regression reasons，并生成对应 reason counts。

重点覆盖：

- maturity narrative summary reasons 被读入 portfolio summary；
- comparison summary 聚合多个 reason counts；
- best-score blocker action evidence 携带 `ci_workflow_regression_reason_counts`；
- recommendation 和 delta explanation 能显示 reason counts；
- CSV、Markdown、HTML 输出包含新增字段和文本。

这些断言保护的是完整链路，而不是单纯检查字段存在。

## 数据结构说明

输入来自 maturity narrative summary：

```json
{
  "release_readiness_ci_workflow_regression_reasons": [
    "ci_failed_checks_increased"
  ],
  "release_readiness_ci_workflow_regression_reason_counts": {
    "ci_failed_checks_increased": 1
  }
}
```

portfolio comparison 输出中对应为：

```json
{
  "maturity_release_readiness_ci_workflow_regression_reasons": [
    "ci_failed_checks_increased"
  ],
  "maturity_release_readiness_ci_workflow_regression_reason_counts": {
    "ci_failed_checks_increased": 1
  }
}
```

summary 聚合后为：

```json
{
  "maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 1
  }
}
```

字段命名有意保留 `maturity_` 前缀，说明原因来自 maturity narrative，而不是 portfolio comparison 自己重新判定。

## 运行流程

```text
load_training_portfolio()
        |
        v
_portfolio_summary()
  - resolve linked maturity_narrative
  - read release_readiness_ci_workflow_regression_reason_counts
        |
        v
_comparison_summary()
  - aggregate maturity CI reason counts
  - expose best-score reason context
        |
        v
build_training_portfolio_review_actions()
  - keep reasons in blocker/review evidence
        |
        v
render/write JSON, CSV, Markdown, HTML
```

这条流程让训练组合比较层不再只拿到一个回归数量，而能在同一份报告里看到原因、阻断建议和可读解释。

## 测试覆盖

本版定向测试运行：

```text
python -m pytest tests/test_training_portfolio_comparison.py -q
```

测试覆盖了 best-score CI order regression、原因聚合、review action evidence、recommendation 文本、delta explanation、CSV 列和 HTML/Markdown 渲染。

完整回归测试和 source encoding hygiene 会在版本收口时一起运行，防止局部字段改动影响其他治理链。

## 证据归档

本版运行截图和说明放在：

```text
d/384/图片
d/384/解释/说明.md
```

`d/384/解释/v384-training-portfolio-maturity-ci-reasons-evidence.html` 是本版人读证据页，用来说明新增字段、测试命令和 Playwright 截图来源。它不是训练产物，也不是下游机器消费源。

## 一句话总结

v384 让 maturity CI regression reasons 从成熟度叙事进入训练组合比较层，使 best-score promotion review 可以直接看到 CI 回归由哪些原因构成。

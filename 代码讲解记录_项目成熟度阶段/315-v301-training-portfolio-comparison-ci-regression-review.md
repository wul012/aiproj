# 315. v301 training portfolio comparison CI regression review

## 本版目标与边界

v301 的目标是把 v300 已经进入 maturity narrative 的 CI workflow regression 和 CI order regression 继续接入 training portfolio comparison。前一版已经让最终成熟度叙事能识别 smoke-before-coverage 顺序漂移；但 portfolio comparison 仍主要消费 coverage regression 字段，导致 best-score portfolio 即使带着 `ci-regressed` 叙事，也可能只表现为普通 maturity review。

所以这一版补的是 promotion 前的比较层拦截：如果最高分 portfolio 的 maturity narrative 显示 CI workflow 或 CI order regression，comparison 会生成 blocker review action，阻止它被当成 clean baseline 继续晋升。

本版不新增新的报告家族，不改变训练、评测、release readiness 或 maturity narrative 的计算方式，也不把 CI 治理信号包装成模型质量下降。它只让现有 maturity narrative 字段进入 portfolio comparison 的决策和 artifact。

## 前置链路

这版承接 v296-v300 的 CI order 证据链：

- v296：CI workflow hygiene 暴露 order counts。
- v297：release bundle 和 release readiness 携带 order counts。
- v298：release readiness comparison 比较 order violation delta。
- v299：registry 和 maturity summary 汇总 order regression。
- v300：maturity narrative 把 order regression 变成 portfolio review 信号。

v301 继续向 training portfolio comparison 推进，让后续 best-score baseline promotion 不需要 reviewer 手动回翻 maturity narrative，比较报告本身就能给出 blocker action。

## 关键文件

- `src/minigpt/training_portfolio_comparison_review.py`
  - 新增 `CI_REGRESSED_TREND = "ci-regressed"`。
  - 新增 `has_maturity_ci_regression()`，同时识别：
    - `maturity_release_readiness_trend == "ci-regressed"`
    - `maturity_release_readiness_ci_workflow_regression_count > 0`
    - `maturity_release_readiness_ci_workflow_order_regression_count > 0`
  - `build_training_portfolio_review_actions()` 现在会为 CI-regressed portfolio 生成 `best_score_ci_regressed` 或 `portfolio_ci_regressed` action。
  - 如果 CI-regressed portfolio 是 best-score，则 severity 为 `blocker`；如果不是 best-score，则保留为 `review`。
  - `build_training_portfolio_recommendations()` 现在会输出 CI workflow regression 的 promotion 阻断建议。

- `src/minigpt/training_portfolio_comparison.py`
  - `_portfolio_summary()` 从 maturity narrative summary 中读取 CI workflow/order regression 字段。
  - `_portfolio_delta()` 输出 CI regression delta 和 CI order regression delta。
  - `_comparison_summary()` 汇总 `maturity_ci_regression_count`、`maturity_ci_regression_names` 和 best-score CI regression 字段。
  - `_delta_explanation()` 在命中 CI regression 时追加 `release-readiness CI regressed`，让比较解释不只显示分数变化。

- `src/minigpt/training_portfolio_comparison_artifacts.py`
  - CSV 增加 CI workflow/order regression count 和 delta 字段。
  - Markdown Summary 增加 Maturity CI regressions 与 portfolio 名称。
  - Markdown/HTML portfolio 表格在 maturity 单元格里显示 `ci`、`ci_order` 和 `coverage` 三类治理信号。
  - HTML stats 增加 CI regressions 和 CI regression portfolios。

- `tests/test_training_portfolio_comparison_review.py`
  - 验证 `has_maturity_ci_regression()` 对字符串数字、`ci-regressed` 状态和非法数字都能容错。
  - 验证 best-score CI order regression 会生成 `best_score_ci_regressed` blocker action。

- `tests/test_training_portfolio_comparison.py`
  - fixture 增加 maturity narrative 的 CI workflow/order regression 字段。
  - 新增 best-score CI order regression 用例，保护 summary、delta、review action、recommendation 和 explanation。
  - 渲染测试保护 Markdown/HTML 中新增的 CI regression 字段。

## 核心字段语义

本版从 maturity narrative summary 消费这些字段：

```text
release_readiness_ci_workflow_regression_count
release_readiness_ci_workflow_order_regression_count
release_readiness_ci_workflow_status_changed_count
release_readiness_max_ci_workflow_failed_check_delta
release_readiness_max_ci_workflow_order_violation_delta
```

进入 portfolio summary 后会变成：

```text
maturity_release_readiness_ci_workflow_regression_count
maturity_release_readiness_ci_workflow_order_regression_count
maturity_release_readiness_ci_workflow_status_changed_count
maturity_release_readiness_max_ci_workflow_failed_check_delta
maturity_release_readiness_max_ci_workflow_order_violation_delta
```

比较 delta 会继续生成：

```text
maturity_release_readiness_ci_workflow_regression_delta
maturity_release_readiness_ci_workflow_order_regression_delta
```

这些字段只表示 release governance 风险，不表示模型输出质量变差。模型分数、验证损失和 benchmark rubric 仍按原有字段独立判断。

## 运行流程

典型链路如下：

```text
maturity_narrative summary
  -> training_portfolio_comparison._portfolio_summary
  -> training_portfolio_comparison._comparison_summary
  -> training_portfolio_comparison_review.build_training_portfolio_review_actions
  -> CSV / Markdown / HTML comparison artifacts
```

如果 best-score portfolio 的 maturity narrative 有：

```text
release_readiness_trend_status=ci-regressed
release_readiness_ci_workflow_order_regression_count=1
```

则 training portfolio comparison 会输出：

```text
maturity_ci_regression_count=1
blocker_action_count=1
reason=best_score_ci_regressed
```

这意味着“最高分”不能直接等同于“可晋升为 clean baseline”。

## 测试覆盖

本版测试覆盖两层：

- review helper 层：
  - 保护 CI regression predicate 的容错输入。
  - 保护 best-score CI regression blocker action。

- comparison 汇总和 artifact 层：
  - 保护 maturity narrative CI 字段读取。
  - 保护 summary 和 delta 输出。
  - 保护 Markdown/HTML 中 CI regression 字段展示。
  - 保护 recommendation 明确提示 CI workflow regression。

这组测试防止后续改动把 CI regression 当成普通 maturity review 或只做展示不参与 blocker 判定。

## 文档与归档

README 当前版本、能力矩阵、成熟度快照、latest checkpoint 和 tag 说明都更新到 v301。

运行截图和解释归档在 `c/301`：

- `c/301/图片/01-training-portfolio-comparison-tests.png`
- `c/301/图片/02-py-compile.png`
- `c/301/图片/03-full-unittest.png`
- `c/301/图片/04-source-encoding.png`
- `c/301/图片/05-coverage-gate.png`
- `c/301/图片/06-docs-code-check.png`

`c/301/解释/说明.md` 说明每张截图证明什么。

## 链路角色

v301 是 CI order governance 链路的 portfolio comparison 消费版。它不再只让 maturity narrative “说出风险”，而是让训练组合比较在选 best-score baseline 前主动阻断带 CI regression 的候选。

一句话总结：v301 把 maturity narrative 的 CI workflow/order regression 变成 training portfolio comparison 的 blocker action，让最高分组合在晋升前也必须满足基本发布治理信号。

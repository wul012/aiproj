# 314. v300 maturity narrative CI order regression review

## 本版目标与边界

v300 的目标是把 v299 已经进入 maturity summary 的 CI workflow order regression 继续接入 maturity narrative。前几版已经让 smoke-before-coverage 顺序漂移从 CI hygiene 进入 project audit、release bundle、release readiness、readiness comparison、registry 和 maturity summary；但最终面向人阅读的 portfolio narrative 还只突出 release regression 与 coverage regression。

所以这一版补的是最后一层消费：让 maturity narrative 的 summary、Release Quality Trend section、Markdown/HTML artifact 和 CLI stdout 都能看到 CI workflow order regression。

本版不新增新的报告家族，不改变训练、推理、release readiness comparison 的计算方式，也不把治理证据包装成模型能力提升。它只让现有治理字段抵达最终叙事层。

## 前置链路

这版承接 v296-v299 的 CI order 证据链：

- v296：CI workflow hygiene 把 order counts 暴露给 CLI stdout 和 project audit context。
- v297：release bundle 和 release readiness 继续携带 order counts。
- v298：release readiness comparison 比较 `ci_workflow_order_violation_delta`。
- v299：registry 与 maturity summary 汇总 `ci_workflow_order_regression_count` 和 `max_abs_ci_workflow_order_violation_delta`。

v300 继续向上推进到 maturity narrative，让 portfolio review 不需要回翻 registry 或 maturity JSON，也能发现 CI order drift。

## 关键文件

- `src/minigpt/maturity.py`
  - `_release_readiness_trend_status()` 现在把 order-only CI workflow regression 也归入 `ci-regressed`。
  - `_recommendations()` 在只有 order regression、没有一般 CI failed-check regression 时，输出明确的 CI workflow order regression review 建议。
  - 这让 maturity summary 本身不再遗漏“CI 仍 pass，但 smoke-before-coverage 顺序变差”的情况。

- `src/minigpt/maturity_narrative_summary.py`
  - `_release_summary()` 从 maturity summary 或 `release_readiness_context` 读取：
    - `ci_workflow_regression_count`
    - `ci_workflow_order_regression_count`
    - `ci_workflow_status_changed_count`
    - `max_abs_ci_workflow_failed_check_delta`
    - `max_abs_ci_workflow_order_violation_delta`
  - `build_maturity_narrative_summary()` 把这些值映射成 `release_readiness_*` 顶层字段。
  - `_portfolio_status()` 把 `ci-regressed`、CI workflow regression 和 CI order regression 都视为 `review` 条件。

- `src/minigpt/maturity_narrative_sections.py`
  - Release Quality Trend claim 增加 CI workflow regression、CI order regression 和 max order violation delta。
  - 这使 narrative section 不只是状态变成 `ci-regressed`，还会解释为什么变成 review。

- `src/minigpt/maturity_narrative_artifacts.py`
  - Markdown Portfolio Summary 增加 Release CI workflow regressions、Release CI order regressions 和 Release CI order delta。
  - HTML stats 增加 CI regressions、CI order regressions 和 CI order delta。
  - CSS 让 `.pill.ci-regressed` 使用红色状态样式，和 release/coverage regression 的视觉语义保持一致。

- `scripts/build_maturity_narrative.py`
  - CLI stdout 增加 CI workflow/order regression 字段。
  - 这给 smoke、CI 日志和截图归档提供稳定可 grep 的命令行证据。

- `tests/test_maturity.py`
  - 新增 order-only CI workflow regression 用例，证明没有 failed-check regression 时，只要 order regression 为 1，maturity 也会进入 `ci-regressed` / `warn`。

- `tests/test_maturity_narrative.py`
  - fixture 增加 CI workflow/order regression 字段。
  - 新增 narrative review 测试，证明 `ci-regressed` 会让 portfolio status 进入 `review`。
  - 输出测试断言 Markdown/HTML 都包含 CI order 字段。

## 核心字段语义

本版没有创造新指标，而是消费 v299 已经建立的字段：

```text
release_readiness_ci_workflow_regression_count
release_readiness_ci_workflow_order_regression_count
release_readiness_ci_workflow_status_changed_count
release_readiness_max_ci_workflow_failed_check_delta
release_readiness_max_ci_workflow_order_violation_delta
```

其中最关键的是：

- `release_readiness_ci_workflow_order_regression_count`
  - 表示跨 readiness comparison 时 CI workflow order violation 变差的次数。
  - 即使 CI job 本身仍然 pass，它也能提示 smoke gate 和 coverage gate 的相对顺序发生了危险漂移。

- `release_readiness_max_ci_workflow_order_violation_delta`
  - 表示 order violation 增量的最大绝对值。
  - 这个字段用于解释漂移幅度，而不是只告诉 reviewer “有回归”。

## 运行流程

典型链路如下：

```text
release_readiness_comparison
  -> registry delta summary
  -> maturity release_readiness_context
  -> maturity_narrative_summary
  -> maturity_narrative_sections
  -> maturity_narrative Markdown / HTML / CLI
```

如果输入 maturity summary 中已有：

```text
release_readiness_trend_status=ci-regressed
release_readiness_ci_workflow_order_regression_count=1
release_readiness_max_ci_workflow_order_violation_delta=1
```

则 maturity narrative 会输出：

```text
portfolio_status=review
Release Quality Trend status=ci-regressed
CI order regressions=1
max order violation delta=1
```

## 测试覆盖

本版测试不是只检查字段存在，而是检查行为：

- `tests.test_maturity`
  - 保护 order-only regression 的 maturity 判定。
  - 防止后续把 `ci_workflow_order_regression_count` 误认为只是展示字段。

- `tests.test_maturity_narrative`
  - 保护 narrative summary 读取字段。
  - 保护 `portfolio_status=review`。
  - 保护 Release Quality Trend claim。
  - 保护 Markdown/HTML artifact 字段展示。

这组测试覆盖了从 maturity summary 到 narrative artifact 的完整消费链。

## 文档与归档

README 当前版本、版本标签、能力矩阵、成熟度快照都更新到 v300。

运行截图和解释归档在 `c/300`：

- `c/300/图片/01-maturity-narrative-tests.png`
- `c/300/图片/02-py-compile.png`
- `c/300/图片/03-maturity-narrative-cli.png`
- `c/300/图片/04-artifact-field-check.png`
- `c/300/图片/05-full-unittest.png`
- `c/300/图片/06-source-encoding.png`
- `c/300/图片/07-coverage-gate.png`
- `c/300/图片/08-docs-code-check.png`

`c/300/解释/说明.md` 说明每张截图证明什么，避免截图只是堆积。

## 链路角色

v300 是 CI order governance 链路的叙事收口版。它不新增底层检查，而是让已经存在的 order regression 指标进入最终 portfolio narrative。

一句话总结：v300 把 CI workflow order regression 从 maturity summary 推进到 maturity narrative，让最终成熟度叙事也能把 smoke-before-coverage 漂移识别为 review 信号。

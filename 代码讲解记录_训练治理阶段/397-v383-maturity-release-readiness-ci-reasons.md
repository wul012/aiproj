# v383 maturity release readiness CI reasons 代码讲解

## 本版目标和边界

v383 的目标是把 v382 registry 汇总出的 release readiness CI workflow regression reasons 带入 maturity summary 和 maturity narrative。

v382 已经让 registry 能在多 run 视角说明 CI 回归原因。v383 解决的是更上层的解释问题：成熟度总结和人读叙事如果只显示 `ci_workflow_regression_count`，reviewer 仍需要回头打开 registry 才能知道原因。现在 maturity summary、maturity narrative、Markdown、HTML 和 CLI 都能展示 reason counts。

本版不新增新的 report 类型，不改变 release readiness comparison 或 registry schema，不扩大到 training portfolio，也不改变 maturity 的整体评分算法。它只沿用现有 release-readiness -> registry -> maturity -> narrative 链路做轻量透传。

## 前置能力

本版承接 v381-v382：

```text
release_readiness_comparison.summary.ci_workflow_regression_reason_counts
        |
        v
registry.release_readiness_delta_summary.ci_workflow_regression_reason_counts
        |
        v
maturity.release_readiness_context.ci_workflow_regression_reason_counts
        |
        v
maturity summary / maturity narrative / CLI / HTML
```

这条链路的意义是：底层 comparison 发现 CI 回归原因，registry 做多 run 聚合，maturity 和 narrative 负责把原因解释给人看。

## 关键文件

### `src/minigpt/maturity.py`

`_release_readiness_context()` 新增两个字段：

```text
ci_workflow_regression_reasons
ci_workflow_regression_reason_counts
```

字段来自 registry 的 `release_readiness_delta_summary`。如果没有 registry 或没有原因字段，列表和映射保持为空，不伪造原因。

`_summary()` 把这两个字段提升到 overview：

```text
release_readiness_ci_workflow_regression_reasons
release_readiness_ci_workflow_regression_reason_counts
```

`_recommendations()` 在 CI workflow regression 或 CI order regression 分支里追加 reason counts，例如：

```text
Review CI workflow hygiene regressions (ci_failed_checks_increased:1, drift_contract_smoke_ready_to_not_ready:1) ...
```

这样成熟度建议不只说“有 CI 回归”，还说明“是哪类 CI 回归”。

### `src/minigpt/maturity_artifacts.py`

Markdown overview 和 Release Readiness Trend Context 新增：

```text
Release readiness CI regression reasons
CI workflow regression reasons
```

HTML stat cards 和 release-readiness 表格也显示同一组 reason counts。这里的产物是最终人读证据，不是新的数据源；下游仍应读取 JSON。

### `src/minigpt/maturity_narrative_summary.py`

`build_maturity_narrative_summary()` 新增：

```text
release_readiness_ci_workflow_regression_reasons
release_readiness_ci_workflow_regression_reason_counts
```

`_release_summary()` 同时支持从 `release_readiness_context` 和 maturity overview 回退读取字段，保持旧 maturity artifact 仍可被 narrative 消费。

`build_maturity_narrative_recommendations()` 在 CI workflow regression 存在时新增 review 建议，并带上 reason counts。这个建议位于通用 `portfolio_status == review` 建议之前，所以能先说明具体 CI 原因，再给出总的组合证据处理建议。

### `src/minigpt/maturity_narrative_sections.py`

`_release_claim()` 在 release quality claim 中加入：

```text
CI regression reasons=...
```

这让叙事 section 的 claim 自己就能解释 CI 回归原因，不需要读者再跳转到 JSON。

### `src/minigpt/maturity_narrative_artifacts.py`

Markdown Portfolio Summary 和 HTML stat cards 新增 CI reason counts 展示。

### CLI 脚本

`scripts/build_maturity_summary.py` 新增 stdout：

```text
release_readiness_ci_workflow_regression_reasons=[...]
release_readiness_ci_workflow_regression_reason_counts={...}
```

`scripts/build_maturity_narrative.py` 输出同名 narrative summary 字段。

CLI 输出的作用是让 CI log 和本地命令行能直接看到原因字段，不必打开 HTML。

## 测试覆盖

`tests/test_maturity.py` 覆盖：

- 默认 registry 没有 CI reason 时，summary 和 release context 输出空 list/dict。
- CI regression fixture 带两个 reason 时，maturity summary、release context 和 recommendation 都保留 reason counts。
- Markdown/HTML 输出包含 CI regression reason 行。

`tests/test_maturity_narrative.py` 覆盖：

- 默认 narrative 输出空 reason list/counts。
- CI-regressed fixture 带 reason counts 时，narrative summary、release section claim 和 recommendation 都能看到同一组原因。
- Markdown/HTML 输出包含 CI reason 展示。

阶段验证：

```text
30 passed
```

最终全量验证：

```text
680 passed
```

source encoding hygiene：

```text
status=pass
source_count=312
clean_count=312
bom_count=0
syntax_error_count=0
```

## 运行证据

运行证据归档在：

```text
d/383/图片/01-maturity-release-readiness-ci-reasons-evidence.png
d/383/解释/说明.md
```

证据页展示 maturity summary、maturity narrative、CLI 输出、测试结果和新增字段位置。

## 一句话总结

v383 让 release readiness CI regression reasons 从 registry 进入 maturity 和 narrative 人读层，使成熟度评审可以直接说明 CI 回归由哪些原因构成。

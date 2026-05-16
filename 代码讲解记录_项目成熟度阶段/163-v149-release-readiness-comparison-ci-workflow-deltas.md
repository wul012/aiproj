# 第一百四十九版代码讲解：release readiness comparison CI workflow deltas

## 本版目标

v149 的目标是把 v148 已经进入 release readiness dashboard 的 CI workflow hygiene 状态继续带入 release readiness comparison。

v145 生成 CI workflow hygiene 报告，v146 让 project audit 审计它，v147 让 release bundle 携带它，v148 让 release readiness dashboard 展示它。v149 解决的是跨版本对比问题：当两个 `release_readiness.json` 比较时，报告应该能看出 CI workflow 状态是否变化、failed check 数是否增加，以及这种变化是否构成 CI hygiene regression。

本版不改变 release gate 的硬规则，不修改 GitHub Actions workflow，不改变模型、训练、推理或 benchmark 逻辑。

## 前置路线

本版承接的证据路线是：

```text
v145 -> ci_workflow_hygiene.json
v146 -> project_audit CI context
v147 -> release_bundle CI evidence
v148 -> release_readiness CI panel
v149 -> release_readiness_comparison CI deltas
```

这条路线让 CI workflow hygiene 从单次检查继续进入跨版本回看，而不是只停留在当前版本 dashboard。

## 关键文件

```text
src/minigpt/release_readiness_comparison.py
tests/test_release_readiness_comparison.py
README.md
c/149/解释/说明.md
```

`src/minigpt/release_readiness_comparison.py` 是核心修改点。它读取每个 readiness report summary 中的 `ci_workflow_status`、`ci_workflow_failed_checks` 和 `ci_workflow_node24_actions`，并把 CI workflow 变化写入 rows、deltas、summary、CSV、Markdown 和 HTML。

`tests/test_release_readiness_comparison.py` 扩展 fixture，让 baseline/current readiness report 都带有 CI workflow 字段和 `ci_workflow_hygiene` panel。

## 核心数据结构

comparison row 新增字段：

```text
ci_workflow_status
ci_workflow_failed_checks
ci_workflow_node24_actions
```

delta 新增字段：

```text
baseline_ci_workflow_status
compared_ci_workflow_status
ci_workflow_failed_check_delta
ci_workflow_status_changed
```

summary 新增字段：

```text
ci_workflow_regression_count
```

这些字段用于说明跨版本 CI hygiene 是否退化，不用于直接阻断发布。

## CI regression 判断

本版新增 `CI_STATUS_ORDER`：

```text
missing/fail -> 0
warn/review  -> 1
pass         -> 2
```

`_is_ci_workflow_regression()` 的判断规则是：

1. 如果 `ci_workflow_failed_check_delta > 0`，认为 CI workflow 退化。
2. 如果 CI workflow status 变差，例如 `pass -> fail`，认为退化。
3. 如果 status 变好，例如 `fail -> pass`，不认为退化。

这个规则避免把所有状态变化都误判为坏变化。

## 输出展示

CSV row 增加：

```text
ci_workflow_status
ci_workflow_failed_checks
```

delta CSV 增加：

```text
ci_workflow_failed_check_delta
ci_workflow_status_changed
```

Markdown Readiness Matrix 增加：

```text
CI workflow
CI failed
```

HTML Readiness Matrix 增加同样两列。

summary 和 HTML stats 增加：

```text
CI workflow regressions
```

## Recommendation 优先级

v149 把 CI workflow regression 放在 recommendation 的较高优先级：

```text
At least one readiness comparison shows CI workflow hygiene regression...
```

原因是 CI workflow hygiene 退化通常来自 workflow 策略、action runtime 或质量步骤遗漏。它未必应该直接阻断 release gate，但应优先提醒人工审查。

## 测试覆盖

`tests/test_release_readiness_comparison.py` 覆盖了：

- 原有 readiness improvement 场景仍然成立。
- 原有 readiness regression 场景仍然成立。
- 新增 CI workflow regression 场景：
  - baseline 是 `ci_workflow_status=pass`。
  - current 是 `ci_workflow_status=fail`、failed checks 增加。
  - 断言 `ci_workflow_regression_count=1`。
  - 断言 delta 含有 `ci_workflow_failed_check_delta=2`。
  - 断言 panel 变化包含 `ci_workflow_hygiene:pass->warn`。
- 输出测试断言 CSV 和 delta CSV 都包含新增 CI workflow 字段。

这些测试证明 v149 是在 release readiness comparison 层消费 v148 的 summary/panel，而不是重新解析 workflow 或改变 release gate。

## 截图与归档

v149 的运行截图和解释放在 `c/149`：

- `01-release-readiness-comparison-tests.png`
- `02-release-readiness-comparison-cli-smoke.png`
- `03-ci-workflow-hygiene-smoke.png`
- `04-source-encoding-smoke.png`
- `05-maintenance-smoke.png`
- `06-full-unittest.png`
- `07-docs-check.png`

这些证据证明 comparison 已经能显示 CI workflow deltas，同时全量测试、源码 hygiene、CI workflow hygiene 和维护 smoke 仍然通过。

## 一句话总结

v149 把 CI workflow hygiene 从单个 release readiness dashboard 推进到跨版本 readiness comparison，让项目能发现 CI 策略退化，但仍不把它变成 release gate 硬阻断。

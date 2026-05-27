# v462 release readiness receipt plan regression

## 本版目标和边界

v461 已经把 `ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready` 带进 release readiness。v462 的目标是让 release readiness comparison 也理解这个字段：当 baseline 为 `True`、current 变成 `False` 或缺失时，比较报告要把它识别成 CI workflow regression。

本版不新增报告链路，不重跑 receipt failure smoke，也不改变 readiness dashboard 的生成规则。它只在已有 comparison 层补一个下游回归识别点。

## 前置链路

本版承接的链路是：

```text
v460 plan check
  -> v461 audit / bundle / readiness carryover
  -> v462 readiness comparison regression detection
```

这和既有的 boundary plan-check、tiny plan digest、drift-contract smoke readiness 是同一类字段：它们都是 CI workflow hygiene 的结构性 ready 信号，整体 release readiness 不下降时也应该被比较层单独捕捉。

## 关键文件

- `src/minigpt/release_readiness_comparison.py`
  - `_row_from_report()` 读取 `ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready`。
  - `_delta_from_baseline()` 生成 baseline/current 字段、changed 字段和 regressed 字段。
  - `_summary()` 汇总 changed/regression count。
  - `_ci_workflow_regression_reasons()` 增加 `receipt_failure_smoke_plan_check_not_ready`。
  - `_ci_workflow_reason_label()` 给该 reason 增加可读说明。
- `src/minigpt/release_readiness_comparison_artifacts.py`
  - CSV 输出新增 receipt plan-check readiness 列。
  - delta CSV 输出新增 receipt plan changed/regressed 列。
  - Markdown/HTML summary、matrix、delta 表格新增 `CI receipt plan` 相关列。
- `scripts/compare_release_readiness.py`
  - CLI 输出 receipt plan-check changed/regression count。
- `tests/test_release_readiness_comparison.py`
  - 新增 ready-to-ready 但 receipt plan-check ready 退化的用例。
  - 更新 CSV、delta CSV、Markdown、HTML 和 CLI 断言。

## 核心字段

row 层字段：

```json
{
  "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready": true
}
```

delta 层字段：

```json
{
  "baseline_ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready": true,
  "compared_ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready": false,
  "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_changed": true,
  "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_regressed": true,
  "ci_workflow_regression_reasons": ["receipt_failure_smoke_plan_check_not_ready"]
}
```

summary 层字段：

```json
{
  "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_changed_count": 1,
  "ci_workflow_promoted_seed_receipt_contract_failure_smoke_plan_check_ready_regression_count": 1,
  "ci_workflow_regression_reason_counts": {
    "receipt_failure_smoke_plan_check_not_ready": 1
  }
}
```

## 判断逻辑

判断规则保持保守：

- 只有 baseline 是 `True` 且 compared 不是 `True` 时，才算 regression。
- `False` 和缺失都会被视为 not-ready，但不会让整体 `delta_status` 强行变成 `regressed`。
- `ci_workflow_regression_count` 会增加，因为这是 CI 证据链退化。

这样可以区分两件事：

- release readiness 状态有没有下降。
- release readiness 背后的 CI 证据有没有退化。

## 测试覆盖

新增用例构造两个都是 `ready/ship/pass` 的 readiness 报告：

- baseline receipt plan-check ready 为 `True`。
- current receipt plan-check ready 为 `False`。

测试断言：

- `ci_workflow_regression_count == 1`
- changed count 和 regression count 都为 `1`
- reason count 为 `{"receipt_failure_smoke_plan_check_not_ready": 1}`
- delta status 仍是 `same`
- explanation 写出 ready 从 `True` 到 `False`
- recommendation 包含 `receipt failure-smoke plan check readiness=1`

Focused 验证结果：

```text
19 passed
```

## 运行证据

`d/462` 保存本版证据：

- `解释/source-inputs/`
  - baseline/current release readiness JSON。
- `解释/release-readiness-comparison-receipt-plan/`
  - comparison JSON、CSV、delta CSV、Markdown、HTML。
- `解释/playwright_receipt_plan_comparison_snapshot.md`
  - Playwright MCP 快照，确认 HTML 中显示 receipt plan changed/regressed 计数和 reason。
- `图片/01-receipt-plan-comparison-regression.png`
  - Playwright MCP 截图，确认页面正常渲染。

## 一句话总结

v462 把 receipt failure-smoke plan-check readiness 从“最终 readiness 可见”推进到“跨版本 comparison 可判定退化”，让 CI 证据退化不会被 overall ready 状态掩盖。

# v244 release readiness coverage dashboard 代码讲解

## 本版目标

v244 的目标是把 coverage gate 证据接入 release readiness dashboard。

v241-v243 已经让 coverage gate 依次进入 project audit、release bundle、release gate policy。v244 补齐最后一层人读看板：发布 readiness 页面能直接看到 coverage status、coverage percent、fail-under 和 gap。

## 不做什么

本版不改变 release gate 的通过规则。

本版不提高 coverage 阈值，仍然消费 `test_coverage_report.json` 中已有的 `fail_under`。

本版不把 coverage pass 解释成模型质量 pass；它只是测试治理证据。

## 前置能力

v240 生成带 `--fail-under 80` 的 coverage gate report。

v241 project audit 读取 coverage report。

v242 release bundle 携带 coverage context 和 report artifacts。

v243 release gate 要求 coverage audit check。

v244 在 readiness dashboard 中展示这些字段。

## 关键文件

### `src/minigpt/release_readiness.py`

`build_release_readiness_dashboard()` 新增参数：

```python
test_coverage_report_path: str | Path | None = None
```

路径解析顺序：

```text
显式 --test-coverage-report
release_bundle.inputs.test_coverage_report_path
<bundle_parent_parent>/test-coverage/test_coverage_report.json
```

readiness panels 新增：

```text
key = test_coverage
title = Test Coverage Gate
```

panel 读取策略：

1. 如果 `test_coverage_report.json` 存在，优先读取其中的 `summary`。
2. 如果独立报告缺失，则回退到 release bundle 的 `summary` 或 `test_coverage_context`。
3. 如果两者都没有，则 panel 为 warn，提示 `test_coverage_report.json missing`。

panel detail 示例：

```text
status=pass; coverage=90.17; fail_under=80; gap=0
```

summary 新增：

```text
test_coverage_status
test_coverage_percent
test_coverage_fail_under
test_coverage_gap
```

这些字段同样优先来自 report，其次来自 bundle summary/context。

### `src/minigpt/release_readiness_artifacts.py`

Markdown summary 新增：

```text
Test coverage
Coverage percent
Coverage fail under
Coverage gap
```

HTML stats 新增：

```text
Coverage
Coverage %
```

这让 readiness 页面和 Markdown 报告都能直接显示覆盖率门禁状态。

### `scripts/build_release_readiness.py`

CLI 新增：

```text
--test-coverage-report <path>
```

终端输出新增：

```text
test_coverage_status
test_coverage_percent
test_coverage_fail_under
test_coverage_gap
```

这使自动化日志也能看到 readiness dashboard 对 coverage gate 的判断。

### `tests/test_release_readiness.py`

测试夹具新增 coverage report、coverage artifact 和 bundle coverage context。

新增测试覆盖：

- dashboard ready 时 summary 包含 coverage status/percent。
- coverage report 缺失时能从 bundle summary/context 回退。
- coverage fail 时 readiness 进入 review。
- Markdown 输出包含 `Test coverage`。

## 输入输出

输入：

```text
release_bundle.json
gate_report.json
project_audit.json
request_history_summary.json
ci_workflow_hygiene.json
test_coverage_report.json
maturity_summary.json
```

输出：

```text
release_readiness.json
release_readiness.md
release_readiness.html
CLI summary lines
```

新增 panel：

```text
Test Coverage Gate
```

## 运行证据

本版运行证据归档在 `c/244`：

- `图片/01-release-readiness-tests.png`
- `图片/02-coverage-gate-smoke.png`
- `图片/03-release-readiness-coverage-smoke.png`
- `图片/04-full-unittest.png`

coverage gate smoke：

```text
Ran 481 tests
status=pass
line_coverage_percent=90.17
fail_under=80.0
coverage_gap=0.0
```

readiness smoke：

```text
readiness_status=ready
decision=ship
gate_status=pass
audit_status=pass
test_coverage_status=pass
test_coverage_percent=90.17
test_coverage_fail_under=80.0
test_coverage_gap=0.0
```

## 测试覆盖

本版验证四层：

1. release readiness 单测覆盖 coverage panel、summary、fallback 和 failed coverage review。
2. release readiness comparison 单测确认旧比较链路未破坏。
3. 真实 smoke 运行 coverage -> audit -> bundle -> gate -> readiness。
4. 全量 unittest 通过，当前共 481 个测试。

## 证据链角色

v244 让 release readiness dashboard 成为 coverage-aware dashboard。

reviewer 不需要跳回 CI 日志或 coverage HTML，就能在 readiness 页面看到 coverage gate 是否 pass、当前覆盖率多少、阈值是多少、差距是多少，以及该证据来自独立 report 还是 bundle context。

## 一句话总结

v244 把 coverage gate 从发布决策层继续带到发布看板层，让最终 readiness 报告能直观看见测试覆盖率门禁证据。

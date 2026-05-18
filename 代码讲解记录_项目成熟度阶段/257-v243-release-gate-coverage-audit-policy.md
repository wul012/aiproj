# v243 release gate coverage audit policy 代码讲解

## 本版目标

v243 的目标是让 release gate 真正消费 v241-v242 已经进入 audit 和 bundle 的 coverage gate 证据。

这版解决的问题是：coverage gate 已经能生成报告，也能进入 project audit 和 release bundle，但 release gate 还没有把 `test_coverage_report` audit check 当成策略条件。v243 让标准发布策略把覆盖率门禁纳入 release approval 判断。

## 不做什么

本版不提高 coverage 阈值，仍然沿用 v240 的 `--fail-under 80`。

本版不让 coverage 结果替代 generation quality、eval suite 或模型 scorecard。

本版不破坏旧 bundle：`legacy` profile 仍允许没有 coverage audit check 的历史 release bundle。

## 前置能力

v239 生成 coverage baseline report。

v240 把 coverage report 变成保守 CI gate。

v241 把 coverage gate status 接入 project audit。

v242 把 coverage gate status 接入 release bundle。

v243 在这个链路末端，把 coverage audit check 接入 release gate policy。

## 关键文件

### `src/minigpt/release_gate.py`

policy profile 新增字段：

```text
require_test_coverage
```

默认策略：

```text
standard = True
review = True
strict = True
legacy = False
```

这和 generation quality、request history 的策略形态一致：当前主线要求 coverage evidence，旧 bundle 兼容 profile 允许缺失。

`resolve_release_gate_policy()` 新增 override：

```python
require_test_coverage: bool | None = None
```

返回 policy 中新增：

```text
require_test_coverage
overrides.require_test_coverage
```

`build_release_gate()` 输出 policy 中新增：

```text
require_test_coverage_audit_check
```

release gate checks 新增：

```text
id = test_coverage_audit_check
title = Test coverage audit check passed
```

检查规则：

```text
require_test_coverage = False -> pass
test_coverage_report missing -> fail
test_coverage_report fail -> fail
test_coverage_report warn -> warn
test_coverage_report pass -> pass
```

summary 新增：

```text
test_coverage_status
test_coverage_percent
test_coverage_fail_under
test_coverage_gap
```

这些字段来自 release bundle summary，不重新解析 coverage report。release gate 的角色是消费 bundle，不再回头读取底层报告。

### `src/minigpt/release_gate_artifacts.py`

Markdown summary 新增：

```text
Test coverage status
Test coverage percent
Test coverage fail under
Test coverage gap
```

HTML stats 新增：

```text
Coverage
Coverage %
```

这样 gate report 一打开就能看到 coverage gate 状态，而不是只能在 check 表里找 `test_coverage_audit_check`。

### `scripts/check_release_gate.py`

CLI 新增：

```text
--allow-missing-test-coverage
```

默认情况下，standard/review/strict 会要求 coverage audit check。该参数用于显式兼容历史 bundle 或临时审查场景。

终端输出新增：

```text
test_coverage_status
test_coverage_percent
test_coverage_fail_under
test_coverage_gap
require_test_coverage
```

### profile comparison

`src/minigpt/release_gate_comparison.py` 和 `scripts/compare_release_gate_profiles.py` 同步新增：

```text
require_test_coverage
--allow-missing-test-coverage
```

comparison row 新增：

```text
require_test_coverage_audit_check
```

delta 新增：

```text
baseline_require_test_coverage
compared_require_test_coverage
```

如果 standard 和 legacy 在 coverage requirement 上不同，delta explanation 会说明：

```text
Test-coverage requirement changes from True to False.
```

### `tests/test_release_gate.py`

测试新增 coverage audit fixture 和三类行为：

- 默认 bundle 带 `test_coverage_report=pass`，standard gate 通过。
- 缺 `test_coverage_report` 时，standard gate fail。
- legacy profile 允许缺 coverage audit check。
- `test_coverage_report=warn` 时，gate 进入 warn。

### `tests/test_release_gate_comparison.py`

profile comparison fixture 同步带 coverage audit check。

这样 standard/review/strict 不会因为测试夹具落后而误判，legacy 的兼容语义仍能在 comparison 中观察到。

## 输入输出

输入：

```text
release_bundle.json
```

release bundle 内部需要包含：

```text
summary.test_coverage_status
summary.test_coverage_percent
summary.test_coverage_fail_under
summary.test_coverage_gap
audit_checks[id=test_coverage_report]
```

输出：

```text
gate_report.json
gate_report.md
gate_report.html
CLI summary lines
```

新增 gate check：

```text
test_coverage_audit_check
```

## 运行证据

本版运行证据归档在 `c/243`：

- `图片/01-release-gate-tests.png`
- `图片/02-coverage-gate-smoke.png`
- `图片/03-release-gate-coverage-smoke.png`
- `图片/04-full-unittest.png`

coverage gate smoke：

```text
Ran 479 tests
status=pass
line_coverage_percent=90.17
fail_under=80.0
coverage_gap=0.0
```

release gate smoke：

```text
gate_status=pass
decision=approved
checks=13 pass/0 warn/0 fail
test_coverage_status=pass
test_coverage_percent=90.17
require_test_coverage=True
```

## 测试覆盖

本版验证四层：

1. release gate 单测：覆盖 coverage audit check 的 pass/missing/warn/legacy 语义。
2. release gate profile comparison 单测：覆盖 coverage policy 字段进入 comparison row/delta。
3. 真实 smoke：coverage -> audit -> bundle -> gate 端到端通过。
4. 全量 unittest 通过，当前共 479 个测试。

## 证据链角色

v243 把 coverage gate 从“报告”和“交接上下文”升级为 release gate policy 的一部分。

但它仍然只证明测试覆盖率门禁干净，不证明模型生成质量。模型能力仍然要看 benchmark suite、generation quality、scorecard、真实 checkpoint 对比和成熟度 narrative。

## 一句话总结

v243 让 coverage gate 进入发布决策层：标准 release gate 不再只看 audit/bundle 完整性，也要求覆盖率门禁的 audit evidence 明确通过。

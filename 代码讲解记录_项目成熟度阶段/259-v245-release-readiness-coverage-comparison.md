# v245 release readiness coverage comparison 代码讲解

## 本版目标

v245 的目标是让 release readiness comparison 能比较 coverage gate 证据。

v244 已经让单个 readiness dashboard 看见 coverage status、percent、fail-under 和 gap。v245 继续往多版本比较层推进：如果当前发布看板相对 baseline 覆盖率下降、coverage gap 变大、coverage panel 从 pass 变 warn，就能在 comparison 报告里明确看到。

## 不做什么

本版不改变 release readiness dashboard 的状态规则。

本版不改变 coverage 阈值，也不重新运行 coverage。

本版不把 coverage regression 解释为模型能力 regression；它只说明测试治理证据退步。

## 关键文件

### `src/minigpt/release_readiness_comparison.py`

readiness row 新增：

```text
test_coverage_status
test_coverage_percent
test_coverage_fail_under
test_coverage_gap
```

delta 新增：

```text
baseline_test_coverage_status
compared_test_coverage_status
test_coverage_percent_delta
test_coverage_gap_delta
test_coverage_status_changed
```

regression 判断新增 `_is_test_coverage_regression()`：

```text
coverage percent delta < 0 -> regression
coverage gap delta > 0 -> regression
coverage status score 下降 -> regression
```

summary 新增：

```text
test_coverage_regression_count
```

recommendation 也新增优先提示：

```text
At least one readiness comparison shows test coverage regression...
```

coverage regression 的提示优先于 CI workflow regression，因为 coverage 已经进入 release gate policy，若 coverage 退步应先让 reviewer 看见。

### `src/minigpt/release_readiness_comparison_artifacts.py`

CSV row 输出新增 coverage 字段：

```text
test_coverage_status
test_coverage_percent
test_coverage_fail_under
test_coverage_gap
```

delta CSV 新增：

```text
test_coverage_percent_delta
test_coverage_gap_delta
test_coverage_status_changed
```

Markdown matrix 新增：

```text
Coverage
Coverage %
Coverage gap
```

Markdown delta 表新增：

```text
Coverage % delta
Coverage gap delta
```

HTML 表格同步展示这些字段。

### `scripts/compare_release_readiness.py`

CLI 输出新增：

```text
ci_workflow_regressions
test_coverage_regressions
```

这样脚本运行日志可以直接看到是否有 coverage regression。

### `tests/test_release_readiness_comparison.py`

测试 fixture 新增：

```text
test_coverage_status
test_coverage_percent
test_coverage_gap
```

新增测试：

```text
test_build_release_readiness_comparison_flags_test_coverage_regression
```

它构造 baseline：

```text
coverage=90.17
gap=0.0
panel=test_coverage:pass
```

再构造 current：

```text
coverage=76.0
gap=4.0
panel=test_coverage:warn
```

断言：

```text
test_coverage_regression_count = 1
test_coverage_percent_delta = -14.17
test_coverage_gap_delta = 4
changed_panels contains test_coverage:pass->warn
```

## 输入输出

输入：

```text
release_readiness.json baseline
release_readiness.json current
```

输出：

```text
release_readiness_comparison.json
release_readiness_comparison.csv
release_readiness_deltas.csv
release_readiness_comparison.md
release_readiness_comparison.html
CLI summary lines
```

## 运行证据

本版运行证据归档在 `c/245`：

- `图片/01-readiness-comparison-tests.png`
- `图片/02-readiness-comparison-coverage-smoke.png`
- `图片/03-readiness-comparison-markdown.png`
- `图片/04-full-unittest.png`

smoke 构造了两个 readiness：

```text
baseline: coverage=90.17, gap=0.0, test_coverage panel pass
current:  coverage=76.0, gap=4.0, test_coverage panel warn
```

comparison 输出：

```text
readiness=2
regressed=1
changed_panel_deltas=1
ci_workflow_regressions=0
test_coverage_regressions=1
```

Markdown 里能看到：

```text
Coverage % delta = -14.17
Coverage gap delta = 4
test_coverage:pass->warn
```

## 测试覆盖

本版验证四层：

1. release readiness comparison 单测覆盖 coverage regression。
2. release readiness dashboard 单测确认 v244 看板输入仍兼容。
3. smoke 命令验证 CLI、JSON、Markdown 输出字段。
4. 全量 unittest 通过，当前共 482 个测试。

## 证据链角色

v245 把 coverage gate 从单个 readiness 看板推进到跨版本 readiness 比较。

这让发布评审可以回答一个更实际的问题：这一版发布看起来仍然能跑，但覆盖率证据是否比 baseline 退步了？

## 一句话总结

v245 让 release readiness comparison 具备 coverage regression 感知能力，可以在发布对比报告中明确指出覆盖率下降、gap 增大和 coverage panel 状态变化。

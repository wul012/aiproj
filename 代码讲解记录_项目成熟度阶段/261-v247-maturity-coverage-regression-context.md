# v247 maturity coverage regression context 代码讲解

## 本版目标

v247 的目标是让 maturity summary 消费 registry 中的 coverage regression。

v246 已经把 release readiness comparison 里的 coverage regression 接入 registry。v247 再往上推进一层：maturity summary 读取 registry 的 `release_readiness_delta_summary`，把 test coverage regression 纳入 overview、release readiness trend context、Markdown/HTML 输出、CLI 输出和 recommendations。

## 不做什么

本版不重新计算 coverage。

本版不改变 `scripts/run_test_coverage.py` 的覆盖率阈值。

本版不改变 registry 的 coverage regression 判断逻辑。

本版不把 coverage regression 解释为模型能力下降；它只代表测试治理证据相对 baseline 退步。

## 前置链路

本版承接 v239-v246：

```text
v239 coverage baseline
v240 coverage fail-under gate
v241 project audit coverage context
v242 release bundle coverage context
v243 release gate coverage audit policy
v244 release readiness coverage dashboard
v245 release readiness coverage comparison
v246 registry coverage regression tracking
v247 maturity coverage regression context
```

这条链路说明 coverage 已经从 CI 里的数字，逐步成为 release review 和 maturity review 都能读到的治理信号。

## 关键文件

### `src/minigpt/maturity.py`

`_release_readiness_context()` 从 registry 的 delta summary 新增读取：

```text
test_coverage_regression_count
test_coverage_status_changed_count
max_abs_test_coverage_percent_delta
max_abs_test_coverage_gap_delta
```

`_release_readiness_trend_status()` 新增优先级：

```text
test_coverage_regression_count > 0 -> coverage-regressed
regressed_count > 0 -> regressed
ci_workflow_regression_count > 0 -> ci-regressed
```

这个顺序让 coverage regression 能独立出现在 maturity summary 里，不会被普通 panel changed 或 improved 计数盖掉。

`_summary()` 新增 overview 字段：

```text
release_readiness_test_coverage_regression_count
release_readiness_test_coverage_status_changed_count
release_readiness_max_test_coverage_percent_delta
release_readiness_max_test_coverage_gap_delta
```

同时，如果 trend 是：

```text
coverage-regressed
```

且原本 maturity 是 `pass`，会降为：

```text
warn
```

这和已有的 `regressed`、`ci-regressed` 一致，表示成熟度评审需要 review。

`_recommendations()` 新增 coverage regression 建议：

```text
Review test coverage regressions before presenting the project as release-stable...
```

### `src/minigpt/maturity_artifacts.py`

Markdown Overview 新增：

```text
Release readiness test coverage regressions
```

Release Readiness Trend Context 新增：

```text
Test coverage regressions
Test coverage status changes
Max coverage percent delta
Max coverage gap delta
```

HTML stats 新增：

```text
Coverage regressions
```

HTML 的 Release Readiness Trend Context 表格也同步展示 coverage regression 字段。

### `scripts/build_maturity_summary.py`

CLI 输出新增：

```text
release_readiness_test_coverage_regression_count
release_readiness_test_coverage_status_changed_count
```

这样运行截图和 CI log 不用打开 JSON 就能看出 maturity review 是否因为 coverage regression 变成 warn。

### `tests/test_maturity.py`

`make_project()` 的 registry fixture 加入 coverage delta summary 字段。

新增测试：

```text
test_test_coverage_regression_marks_maturity_for_review
```

它构造：

```text
release_readiness_comparison_counts={"coverage-regressed": 1}
test_coverage_regression_count=1
test_coverage_status_changed_count=1
max_abs_test_coverage_percent_delta=7.5
max_abs_test_coverage_gap_delta=3
```

断言：

```text
release_readiness_trend_status == "coverage-regressed"
overall_status == "warn"
recommendations contains "test coverage regressions"
```

### `tests/test_maturity_artifacts.py`

artifact split 测试新增 Markdown/HTML 断言：

```text
Test coverage regressions
Coverage regressions
```

这保护人读输出不会只在 JSON 里有字段。

## 输入输出

输入仍然是 maturity summary 的项目根目录和可选 registry：

```text
python scripts/build_maturity_summary.py --project-root . --registry runs/registry/registry.json
```

registry 需要包含：

```text
release_readiness_delta_summary.test_coverage_regression_count
release_readiness_delta_summary.test_coverage_status_changed_count
release_readiness_delta_summary.max_abs_test_coverage_percent_delta
release_readiness_delta_summary.max_abs_test_coverage_gap_delta
```

输出仍然是：

```text
maturity_summary.json
maturity_summary.csv
maturity_summary.md
maturity_summary.html
CLI summary lines
```

## 运行证据

本版运行证据归档在 `c/247`：

- `图片/01-maturity-coverage-tests.png`
- `图片/02-maturity-coverage-smoke.png`
- `图片/03-maturity-coverage-output-check.png`
- `图片/04-full-unittest.png`

smoke 样本中 registry 包含：

```text
release_readiness_comparison_counts={"coverage-regressed": 1, "improved": 1}
test_coverage_regression_count=1
test_coverage_status_changed_count=1
max_abs_test_coverage_percent_delta=7.5
max_abs_test_coverage_gap_delta=3
```

maturity 输出：

```text
overall_status=warn
release_readiness_trend_status=coverage-regressed
```

## 证据链角色

v247 把 coverage regression 从 registry 的多 run 索引维度，提升成 maturity review 的风险维度。

这让项目说明时可以更诚实地区分：

```text
模型能力是否提升
发布治理证据是否退步
测试覆盖率是否回落
```

## 一句话总结

v247 让 maturity summary 具备 coverage regression 感知能力：覆盖率退步会进入成熟度总览、趋势上下文、输出报告和 review 建议。

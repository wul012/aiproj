# v249 coverage governance chain test 代码讲解

## 本版目标

v249 的目标是给 coverage governance 主链加端到端回归测试。

v239-v248 已经把 coverage 证据一路推到 maturity narrative。继续新增展示层收益已经不高，所以本版做收口：新增一个测试文件，真实构造 readiness coverage regression，然后依次经过：

```text
release readiness comparison
run registry
maturity summary
maturity narrative
```

最后断言 `coverage-regressed` 能走完整条链路，并让 maturity/narrative 进入 review。

## 不做什么

本版不改生产代码。

本版不改变 coverage threshold。

本版不改变 registry、maturity summary 或 maturity narrative 的判断规则。

本版不新增报告格式或 UI。

## 关键文件

### `tests/test_coverage_governance_chain.py`

这是本版唯一新增的测试文件。

测试入口：

```text
CoverageGovernanceChainTests.test_coverage_regression_flows_from_readiness_comparison_to_maturity_narrative
```

它做四步。

第一步，构造 baseline 和 current readiness：

```text
baseline:
  readiness_status=ready
  test_coverage_status=pass
  test_coverage_percent=90.17
  test_coverage_gap=0

current:
  readiness_status=review
  test_coverage_status=fail
  test_coverage_percent=76.0
  test_coverage_gap=4
```

然后调用：

```text
build_release_readiness_comparison()
write_release_readiness_comparison_outputs()
```

断言 comparison 层输出：

```text
test_coverage_regression_count == 1
test_coverage_percent_delta == -14.17
test_coverage_gap_delta == 4
```

第二步，构造带有 `run_manifest.json` 的 run 目录，并把 comparison 输出放入：

```text
runs/demo-run/release-readiness-comparison/release_readiness_comparison.json
```

然后调用：

```text
build_run_registry()
write_registry_outputs()
```

断言 registry 层输出：

```text
release_readiness_comparison_counts == {"coverage-regressed": 1}
release_readiness_delta_summary.test_coverage_regression_count == 1
release_readiness_delta_summary.max_abs_test_coverage_gap_delta == 4
```

第三步，调用：

```text
build_maturity_summary()
write_maturity_summary_outputs()
```

断言 maturity summary 层输出：

```text
overall_status == "warn"
release_readiness_trend_status == "coverage-regressed"
release_readiness_test_coverage_regression_count == 1
```

第四步，补齐 narrative 需要的 request-history、benchmark-scorecard、scorecard-decision、dataset-card fixtures，然后调用：

```text
build_maturity_narrative()
write_maturity_narrative_outputs()
```

断言 narrative 层输出：

```text
portfolio_status == "review"
release_readiness_trend_status == "coverage-regressed"
release_readiness_test_coverage_regression_count == 1
release_section.status == "coverage-regressed"
release_section.claim contains "test coverage regressions=1"
recommendations contains "Resolve review-level release"
```

## 输入输出

这个测试不依赖仓库里的真实运行产物，而是在临时目录中构造最小 fixtures。

输入 fixture：

```text
release_readiness.json baseline/current
run_manifest.json
request_history_summary.json
benchmark_scorecard.json
benchmark_scorecard_decision.json
dataset_card.json
README version tags
archive version directories
```

输出 artifact：

```text
release_readiness_comparison.json
registry.json
maturity_summary.json
maturity_narrative.json/html
```

所有这些输出都在 `tempfile.TemporaryDirectory()` 下生成，测试结束后自动清理。

## 测试覆盖意义

单测已经分别覆盖了 v245、v246、v247、v248 的局部行为。

v249 补的是跨模块契约：

```text
comparison 字段名不能变
registry 必须继续读取 comparison summary/delta
maturity summary 必须继续读取 registry delta summary
narrative 必须继续读取 maturity coverage context
```

这比再多加一个报告字段更有价值，因为它能防止后续重构时“上游测试都过，但下游消费断了”的问题。

## 运行证据

本版运行证据归档在 `c/249`：

- `图片/01-coverage-governance-chain-tests.png`
- `图片/02-coverage-governance-neighborhood-tests.png`
- `图片/03-coverage-governance-structure-check.png`
- `图片/04-full-unittest.png`

关键验证：

```text
python -B -m unittest tests.test_coverage_governance_chain -q
Ran 1 test OK

python -B -m unittest discover -s tests -q
Ran 486 tests OK
```

## 证据链角色

v249 是 coverage governance 系列的收口型版本。

它不增加功能表面，而是把 v239-v248 的关键链路变成测试契约。后续无论拆 registry、maturity 还是 narrative，只要 coverage regression 信号断掉，这个测试就会失败。

## 一句话总结

v249 用端到端集成测试守住 coverage governance 主链，让覆盖率退步信号必须从 readiness comparison 传到 maturity narrative review。

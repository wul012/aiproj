# v246 registry coverage regression tracking 代码讲解

## 本版目标

v246 的目标是把 v245 的 release readiness coverage regression 接入 run registry。

v245 已经让多个 `release_readiness.json` 之间可以比较 coverage status、coverage percent、coverage gap 和 panel 变化。v246 继续往 registry 推进：当某个 run 下存在 `release-readiness-comparison/release_readiness_comparison.json` 时，registry 能读出 coverage regression，并在 JSON、CSV、HTML、leaderboard 和 CLI 中呈现。

## 不做什么

本版不重新计算 coverage。

本版不改变 `scripts/run_test_coverage.py` 的 `--fail-under` 行为。

本版不改变 release readiness 或 release gate 的通过规则。

本版也不把 coverage regression 解释为模型质量下降；它只表示测试治理证据相对 baseline 退步。

## 前置能力

本版承接 v239-v245 的 coverage 证据链：

```text
v239 coverage baseline
v240 coverage fail-under gate
v241 project audit coverage context
v242 release bundle coverage context
v243 release gate coverage audit policy
v244 release readiness coverage dashboard
v245 release readiness coverage comparison
v246 registry coverage regression tracking
```

这条链路的意义是：coverage 不再只是 CI 输出，而是一路进入 audit、bundle、gate、readiness、comparison，最终进入 registry 多 run 索引。

## 关键文件

### `src/minigpt/registry_data.py`

`RegisteredRun` 新增字段：

```text
release_readiness_test_coverage_regression_count
```

`summarize_registered_run()` 从 comparison summary 读取：

```text
test_coverage_regression_count
```

`_release_readiness_comparison_status()` 新增优先级：

```text
test_coverage_regression_count > 0 -> coverage-regressed
ci_workflow_regression_count > 0 -> ci-regressed
regressed_count > 0 -> regressed
```

这个顺序是有意的：coverage regression 是 v245 新增的发布证据退步信号，进入 registry 后应该能被直接筛出，而不是被普通 panel-changed 或 CI 状态遮住。

### `src/minigpt/registry_rankings.py`

`collect_release_readiness_delta_rows()` 新增读取 delta 字段：

```text
baseline_test_coverage_status
compared_test_coverage_status
test_coverage_percent_delta
test_coverage_gap_delta
test_coverage_status_changed
```

`release_readiness_delta_summary()` 新增：

```text
test_coverage_regression_count
test_coverage_status_changed_count
max_abs_test_coverage_percent_delta
max_abs_test_coverage_gap_delta
```

`_is_test_coverage_regression_row()` 的判断规则和 v245 comparison 保持一致：

```text
percent delta < 0 -> regression
gap delta > 0 -> regression
coverage status score 下降 -> regression
```

`release_readiness_delta_leaderboard()` 的排序也加入 coverage regression 优先级。这样 registry 的 delta leader 会优先把 coverage 退步 run 展示出来。

### `src/minigpt/registry_artifacts.py`

registry CSV 新增：

```text
release_readiness_test_coverage_regression_count
```

这让后续脚本、表格或外部汇总可以不用解析 HTML，就能直接读取 coverage regression 计数。

### `src/minigpt/registry_render.py`

HTML 顶部 stats 新增：

```text
Coverage regressions
```

Release Readiness cell 新增：

```text
coverage regressions=<count>
```

搜索字段新增 `release_readiness_test_coverage_regression_count`，因此 registry 页面搜索 coverage regression 数字或相关字段时不会漏掉这一信号。

### `src/minigpt/registry_leaderboards.py`

Release Readiness Deltas 表新增 Coverage 列：

```text
baseline_test_coverage_status -> compared_test_coverage_status
percent=<delta>
gap=<delta>
```

这是人读 dashboard 最直接的证据：reviewer 可以看到覆盖率是从 `pass` 到 `fail`，还是仅仅 gap 数值变大。

### `scripts/register_runs.py`

CLI 输出新增：

```text
release_readiness_coverage_regressions=<count>
```

这行适合 CI log、截图归档和快速人工检查。

## 输入输出

输入仍然是 run 目录：

```text
run/
  run_manifest.json
  release-readiness-comparison/
    release_readiness_comparison.json
```

其中 comparison JSON 的 summary 至少包含：

```text
test_coverage_regression_count
```

delta 至少包含：

```text
baseline_test_coverage_status
compared_test_coverage_status
test_coverage_percent_delta
test_coverage_gap_delta
test_coverage_status_changed
```

输出为 registry 产物：

```text
registry.json
registry.csv
registry.svg
registry.html
CLI summary lines
```

## 测试覆盖

`tests/test_registry.py` 的 `make_run()` 增加 `readiness_coverage_regression` fixture 开关。

新增或扩展的关键断言包括：

```text
run.release_readiness_comparison_status == "coverage-regressed"
run.release_readiness_test_coverage_regression_count == 1
registry["release_readiness_delta_summary"]["test_coverage_regression_count"] == 1
registry["release_readiness_delta_summary"]["max_abs_test_coverage_percent_delta"] == 7.5
registry["release_readiness_delta_summary"]["max_abs_test_coverage_gap_delta"] == 3
registry["release_readiness_delta_leaderboard"][0]["test_coverage_gap_delta"] == 3
```

输出层测试确认：

```text
CSV contains release_readiness_test_coverage_regression_count
HTML contains Coverage regressions
HTML contains Coverage column
```

`tests.test_registry_split` 也一起跑，保护 registry facade、data、artifact、render 分层没有被这次新增字段打破。

## 运行证据

本版运行证据归档在 `c/246`：

- `图片/01-registry-coverage-tests.png`
- `图片/02-registry-coverage-smoke.png`
- `图片/03-registry-coverage-output-check.png`
- `图片/04-full-unittest.png`

smoke 构造了两个 run：

```text
stable: readiness improved
coverage-drop: readiness panel-changed, coverage pass -> fail, percent -7.5, gap +3
```

registry 输出：

```text
release_readiness_comparison_counts={"improved": 1, "coverage-regressed": 1}
test_coverage_regression_count=1
max_abs_test_coverage_percent_delta=7.5
max_abs_test_coverage_gap_delta=3
```

## 证据链角色

v246 把 coverage regression 从“单次 readiness comparison 的局部发现”提升为“registry 多 run 索引维度”。

这让后续 maturity summary、portfolio review 或外部 dashboard 可以直接消费 registry，而不需要逐个打开每个 run 的 readiness comparison 文件。

## 一句话总结

v246 让 run registry 具备 coverage regression 感知能力，把覆盖率退步信号纳入实验登记、导出、排序和人读 dashboard。

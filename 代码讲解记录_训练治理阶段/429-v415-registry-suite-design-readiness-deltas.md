# v415 registry release readiness suite design deltas

## 本版目标和边界

v415 的目标是把 v414 的 release-readiness comparison suite-design delta 接入 registry。这样 registry 不只知道 release readiness 是否 coverage-regressed、benchmark-regressed 或 ci-regressed，也能知道 benchmark history regression 里是否包含 prompt-suite design not-ready 增量。

本版不重新计算 comparison、不定义新的 suite-design 质量规则、不训练模型，也不扩展到 maturity summary。它只消费 comparison 产物，生成 registry 层的索引、排序、CSV/HTML 和 CLI 输出。

## 前置能力

本版承接：

- v413：release readiness dashboard 记录 suite-design not-ready 与 design-change 计数。
- v414：release readiness comparison 计算 suite-design not-ready delta 和 design-comparison changed delta。

v415 位于 registry 层，负责把多 run 的 comparison delta 汇总成可检索、可排序、可审阅的注册表证据。

## 关键文件

### `src/minigpt/registry_release_readiness.py`

`collect_release_readiness_delta_rows()` 新增两个 row 字段：

```text
benchmark_history_suite_design_non_comparison_ready_entries_delta
benchmark_history_design_comparison_changed_entries_delta
```

`release_readiness_delta_summary()` 新增：

```text
benchmark_history_suite_design_non_comparison_ready_delta_count
benchmark_history_suite_design_non_comparison_ready_regression_count
benchmark_history_design_comparison_changed_delta_count
max_abs_benchmark_history_suite_design_non_comparison_ready_entries_delta
max_abs_benchmark_history_design_comparison_changed_entries_delta
```

`_is_benchmark_history_regression_row()` 把 suite-design not-ready 正向增量视为 benchmark-history regression。leaderboard 排序也把 suite/design delta 纳入优先级。

### `src/minigpt/registry_data.py`

`RegisteredRun` 新增短字段：

```text
release_readiness_benchmark_suite_design_delta_count
release_readiness_benchmark_suite_design_regression_count
release_readiness_benchmark_design_change_delta_count
```

这些字段来自 comparison summary；当 summary 缺失时，可从 deltas 回退计算。

### `src/minigpt/registry_artifacts.py`

registry CSV 增加：

```text
release_readiness_benchmark_suite_design_delta_count
release_readiness_benchmark_suite_design_regression_count
release_readiness_benchmark_design_change_delta_count
```

### `src/minigpt/registry_render.py`

registry HTML 增加：

- `Benchmark suite-design` stat card。
- run row 的 `suite design deltas=<n> regressions=<n> changes=<n>`。
- benchmark summary label 中的 suite delta max。

这些是 registry 可视化，不是新的模型质量证明。

### `src/minigpt/registry_leaderboards.py`

Release Readiness Deltas leaderboard 的 benchmark history cell 增加：

```text
suite=<delta> design=<delta>
```

### `scripts/register_runs.py`

stdout 新增：

```text
release_readiness_benchmark_suite_design_delta_count
release_readiness_benchmark_suite_design_regression_count
release_readiness_benchmark_design_change_delta_count
```

## 测试覆盖

`tests/test_registry.py` 新增和更新：

- suite-design regression fixture。
- `summarize_registered_run()` 读取 suite-design delta/regression。
- `build_run_registry()` 汇总 suite-design delta count、regression count、design-change count 和 max abs delta。
- leaderboard row 保留 suite/design delta。
- registry CSV/HTML 显示新增字段。
- `scripts/register_runs.py` stdout 输出新增 summary。

## 验证命令

```text
python -m pytest tests\test_registry.py -q
python -m py_compile src\minigpt\registry_release_readiness.py src\minigpt\registry_data.py src\minigpt\registry_artifacts.py src\minigpt\registry_render.py src\minigpt\registry_leaderboards.py scripts\register_runs.py tests\test_registry.py
python -m pytest -q
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v415
git diff --check
```

结果：registry 定向测试 `18 passed`，全量 pytest `705 passed`，source encoding hygiene `status=pass` 且 `319` 个 source clean，`git diff --check` 无 whitespace error。

## 运行证据

运行截图与说明归档在：

```text
d/415/图片/01-registry-suite-design-readiness-deltas-evidence.png
d/415/解释/说明.md
d/415/解释/v415-registry-suite-design-readiness-deltas-evidence.html
```

## 一句话总结

v415 把 release readiness comparison 的 suite-design risk 接入 registry，让多 run 索引也能识别 prompt-suite 设计边界的回归。

# 第一百四十四篇代码讲解：第350版 registry benchmark readiness tracking

本版目标，是把 v349 release readiness comparison 里的 benchmark history regression 信号继续带进 run registry。

v349 已经能在单个 comparison artifact 中说明 benchmark history 从 `pass` 到 `warn`、case regression 增多、generation-flag regression 增多、latest boundary 改变。v350 解决的是多 run 视角：当很多训练 run 放进 registry 时，reviewer 不应该逐个打开 comparison JSON 才知道哪个 run 有 benchmark-history regression。

本版不重新生成 release readiness comparison，不训练模型，也不改变 benchmark history 的判断规则。它只消费已有 comparison summary 和 delta 字段，把它们汇入 registry。

## 本版所处链路

前置链路是：

```text
benchmark history -> release readiness -> release readiness comparison
```

v350 追加的是：

```text
release readiness comparison -> registry
```

它的角色是 multi-run scan：单个 comparison 负责解释一个 release 对比，registry 负责把多个 run 的 readiness trend 放在一个索引里筛查。

## 输入输出

输入仍然是 run 目录中的：

```text
release-readiness-comparison/release_readiness_comparison.json
```

输出仍然是 registry 的四类产物：

```text
registry.json
registry.csv
registry.svg
registry.html
```

新增的是 registry row、delta summary、leaderboard、CSV、HTML 和 `scripts/register_runs.py` stdout 中的 benchmark history readiness 字段。

## 关键文件

`src/minigpt/registry_data.py`

- `RegisteredRun` 新增 `release_readiness_benchmark_history_delta_count`。
- `RegisteredRun` 新增 `release_readiness_benchmark_history_regression_count`。
- `_release_readiness_comparison_status()` 现在能返回 `benchmark-regressed`。
- 优先级保持保守：coverage regression 仍优先于 benchmark regression，因为 coverage gate 属于基础质量门；benchmark regression 单独排在 CI regression 前，避免被泛化成普通 panel change。

`src/minigpt/registry_rankings.py`

- `collect_release_readiness_delta_rows()` 读取 benchmark history status、ready/review/blocked delta、case regression delta、generation-flag regression delta、quality-claim changed 和 boundary changed。
- `release_readiness_delta_summary()` 聚合 benchmark history regression count、status changed count、boundary changed count、最大 case regression delta 和最大 generation-flag regression delta。
- `_is_benchmark_history_regression_row()` 复用 v349 的判断语义：status 变差、ready 变少、review/blocked/regression 变多都算退化。
- leaderboard 排序会把 benchmark-history regression 放在普通 CI regression 前，但仍低于 coverage regression。

`src/minigpt/registry_render.py`

- 顶部 stats 新增 `Benchmark regressions`。
- release readiness summary label 显示 `benchmark:<count>`。
- run 行里的 Release Readiness cell 显示 `benchmark regressions=<n> deltas=<n>`。
- readiness 排序新增 `benchmark-regressed` 状态。

`src/minigpt/registry_leaderboards.py`

- Release Readiness Deltas 表新增 `Benchmark history` 列。
- 每行显示：

```text
baseline_benchmark_history_status -> compared_benchmark_history_status
case=<delta>
flags=<delta>
boundary=<changed>
```

`src/minigpt/registry_artifacts.py`

- registry CSV 新增 run 级 benchmark-history readiness 字段，便于脚本和表格工具筛选。

`scripts/register_runs.py`

- stdout 新增：

```text
release_readiness_benchmark_history_regressions
```

这样命令行 smoke 不必打开 registry JSON，也能确认 v350 是否接入了 v349 的信号。

## 核心数据结构

run 级字段：

```text
release_readiness_benchmark_history_delta_count
release_readiness_benchmark_history_regression_count
```

delta 级字段：

```text
baseline_benchmark_history_status
compared_benchmark_history_status
benchmark_history_status_delta
benchmark_history_ready_delta
benchmark_history_case_regression_delta
benchmark_history_generation_flag_regression_delta
benchmark_history_latest_boundary_changed
baseline_benchmark_history_boundary
compared_benchmark_history_boundary
```

summary 级字段：

```text
benchmark_history_regression_count
benchmark_history_status_changed_count
benchmark_history_boundary_changed_count
max_abs_benchmark_history_case_regression_delta
max_abs_benchmark_history_generation_flag_regression_delta
```

## 测试覆盖

`tests/test_registry.py` 覆盖：

- run summary 能把 benchmark-history regression 识别为 `benchmark-regressed`。
- registry summary 能统计 benchmark-history regression count。
- readiness delta leaderboard 保留 case regression delta 和 boundary changed。
- registry CSV 输出新增字段。
- registry HTML 顶部 stats、run cell、Release Readiness Deltas 表都能显示 benchmark-history 信息。

这些测试保护的是跨层消费，不只是字段存在：v349 生成的 comparison 证据必须在 registry 多 run 索引中可见。

## 运行证据

本版证据归档在：

```text
d/350
```

Playwright 截图里可以看到：

```text
Release readiness: benchmark-regressed:1, improved:1
Readiness deltas: benchmark:1
Benchmark regressions: regressions:1, case:2, flags:1, boundary:1
```

## 边界说明

v350 仍然不把 benchmark-history regression 解释成模型质量下降。它只说明 release readiness comparison 的 evidence boundary 变差。

如果 compared boundary 是 `tiny-smoke-plumbing-evidence`，registry 会把它当成 review 索引信号，而不是把它包装成生产级模型能力判断。

## 一句话总结

v350 把 benchmark-history readiness regression 从单个 comparison artifact 推进到 registry 多 run 索引，让评审可以一眼筛出需要继续查看 benchmark 边界的 run。

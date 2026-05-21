# 384-v370 registry benchmark requirement

## 本版目标和边界

v369 已经让 release readiness dashboard 和 release readiness comparison 识别 benchmark readiness requirement 的失败。v370 继续向下游推进，把这些 requirement delta 带入 registry。

本版不改模型训练、不改 benchmark history 生成、不改 release readiness comparison 的原始 schema 来源。它只消费已有 readiness comparison delta，并让 registry 的 run row、summary、leaderboard、CSV、HTML 和 CLI stdout 能看到 requirement status change 与 exit-code delta。

## 前置链路

前置能力来自：

- v364：benchmark history readiness gate，定义 readiness requirement。
- v365-v368：maturity、audit、bundle、release gate 消费 requirement。
- v369：release readiness 和 readiness comparison 输出 requirement status、exit code、failed reasons 与 delta。

v370 是同一条链路进入多运行目录汇总层的版本。

## 关键文件

- `src/minigpt/registry_rankings.py`
  - `collect_release_readiness_delta_rows()` 从 readiness comparison delta 读取 requirement status、exit-code delta、failed reasons。
  - `release_readiness_delta_summary()` 统计 requirement status changed count 和 max abs exit-code delta。
  - `_is_benchmark_history_regression_row()` 把 requirement 从 `pass` 退到 `fail` 或 exit-code 正向增加视为 benchmark-history regression。
  - `release_readiness_delta_leaderboard()` 把 requirement change 和 exit-code delta 纳入排序权重。
- `src/minigpt/registry_data.py`
  - `RegisteredRun` 新增 `release_readiness_benchmark_requirement_status_change_count` 与 `release_readiness_benchmark_requirement_exit_code_delta_max`。
  - `summarize_registered_run()` 从单个 run 的 readiness comparison deltas 提升这两个字段，供 CSV、HTML、搜索使用。
- `src/minigpt/registry_artifacts.py`
  - `registry.csv` 新增两个 run 级字段，方便脚本或表格审阅。
- `src/minigpt/registry_render.py`
  - 顶部 Readiness deltas 和 Benchmark regressions stat card 显示 requirement change 与 exit delta。
  - run 表格的 Release Readiness cell 显示 `benchmark req changes` 和 `exit max`。
  - 搜索文本纳入新字段。
- `src/minigpt/registry_leaderboards.py`
  - Release Readiness Deltas 表格的 Benchmark history 列显示 `req=pass -> fail exit=+1`。
- `scripts/register_runs.py`
  - CLI stdout 新增 `release_readiness_benchmark_requirement_status_changes` 和 `release_readiness_benchmark_requirement_exit_delta_max`。
- `tests/test_registry.py`
  - 测试 fixture 构造 requirement 从 pass 到 fail 的 delta。
  - 覆盖 run 字段、registry summary、leaderboard、CSV 字段、HTML 文本。

## 核心数据结构

readiness comparison delta 已经包含：

```json
{
  "baseline_benchmark_history_readiness_requirement_status": "pass",
  "compared_benchmark_history_readiness_requirement_status": "fail",
  "benchmark_history_readiness_requirement_status_changed": true,
  "benchmark_history_readiness_requirement_exit_code_delta": 1,
  "compared_benchmark_history_readiness_requirement_failed_reasons": ["insufficient_ready_entries"]
}
```

registry summary 新增聚合字段：

```json
{
  "benchmark_history_readiness_requirement_status_changed_count": 1,
  "max_abs_benchmark_history_readiness_requirement_exit_code_delta": 1
}
```

run row 新增字段：

```json
{
  "release_readiness_benchmark_requirement_status_change_count": 1,
  "release_readiness_benchmark_requirement_exit_code_delta_max": 1
}
```

这些字段的角色不同：delta 字段保留单次比较的详细原因，summary 字段供 registry 总览和排序使用，run row 字段供 CSV、搜索和表格 cell 使用。

## 运行流程

1. `scripts/register_runs.py` 收集多个 run 目录。
2. `summarize_registered_run()` 读取每个 run 的 `release-readiness-comparison/release_readiness_comparison.json`。
3. `registry_rankings.collect_release_readiness_delta_rows()` 展平所有 readiness deltas。
4. `release_readiness_delta_summary()` 汇总 benchmark-history regression、requirement status changed count 和 exit-code delta。
5. `write_registry_outputs()` 写出 JSON、CSV、SVG、HTML。
6. HTML 页面顶部 stat card、run 表格、Release Readiness Deltas 表格同时显示 requirement 变化。

## 测试覆盖

- `test_summarize_registered_run_reads_benchmark_history_readiness_regression`
  - 断言 run 级字段能读到 requirement status change 和 exit-code delta。
- `test_build_registry_picks_best_and_counts_quality`
  - 断言 registry summary 统计 `benchmark_history_readiness_requirement_status_changed_count=1`。
  - 断言 leaderboard row 保留 compared requirement status 和 exit-code delta。
- `test_write_registry_outputs`
  - 断言 CSV 包含新增字段。
  - 断言 HTML 包含 `benchmark req changes=1 exit max=1` 和 `req=pass -> fail exit=+1`。

## 运行截图和证据

- `d/370/图片/01-registry-benchmark-requirement.png`
- `d/370/解释/说明.md`
- `d/370/解释/playwright-check.txt`

截图和 Playwright 检查证明 registry HTML 已经能直接显示 benchmark readiness requirement 的变化。`runs/registry-v370` 是生成截图时的中间产物，不作为最终版本归档提交。

一句话总结：v370 让 benchmark readiness requirement 的失败从 readiness comparison 进入 registry 多运行审阅面，减少只看旧 benchmark status 而漏掉 requirement 失败的风险。

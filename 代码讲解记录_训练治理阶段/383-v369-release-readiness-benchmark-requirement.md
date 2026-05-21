# 383-v369 release readiness benchmark requirement

## 本版目标和边界

v368 已经让 release gate 消费 benchmark history readiness requirement。v369 继续向下游推进一层，把这份 requirement 带入 release readiness dashboard 和 release readiness comparison。

本版不改模型训练、不改 benchmark history 的生成逻辑，也不改 release gate 的决策规则。它只处理 readiness summary、benchmark panel、readiness comparison row/delta、CSV/Markdown/HTML 和 CLI stdout。

## 关键文件

- `src/minigpt/release_readiness.py`
  - `_benchmark_history_summary()` 从 gate summary 或 bundle summary 读取 requirement status、exit code 和 failed reasons。
  - `_benchmark_history_panel()` 在 panel detail 中显示 requirement 诊断字段。
  - `_benchmark_history_panel_status()` 让 requirement `fail` 或 exit code 非零把 benchmark panel 降为 `warn`，避免 summary 显示失败但 panel 仍为 pass。

- `src/minigpt/release_readiness_artifacts.py`
  - Markdown summary 增加 benchmark readiness、exit 和 reasons。
  - HTML stats 增加 `Bench readiness` 和 `Bench readiness exit`。

- `src/minigpt/release_readiness_comparison.py`
  - readiness row 增加 requirement status、exit code 和 failed reasons。
  - delta 增加 requirement status changed、exit-code delta、baseline/current failed reasons。
  - benchmark regression 判断新增 requirement fail 和 exit-code regression。

- `src/minigpt/release_readiness_comparison_artifacts.py`
  - CSV、delta CSV、Markdown matrix、HTML matrix 和 delta table 都输出 requirement 字段。

- `scripts/build_release_readiness.py`
  - stdout 输出 readiness requirement status、exit code 和 failed reasons。

- `scripts/compare_release_readiness.py`
  - stdout 按 release 打印 requirement status 和 exit code，方便从 CI 日志里直接看到回退来源。

## 核心数据结构

release readiness summary 输入和输出保留这些字段：

```json
{
  "benchmark_history_status": "pass",
  "benchmark_history_readiness_requirement_status": "fail",
  "benchmark_history_readiness_requirement_exit_code": 1,
  "benchmark_history_readiness_requirement_failed_reasons": ["insufficient_ready_entries"]
}
```

readiness comparison delta 增加：

```json
{
  "benchmark_history_readiness_requirement_status_changed": true,
  "baseline_benchmark_history_readiness_requirement_status": "pass",
  "compared_benchmark_history_readiness_requirement_status": "fail",
  "benchmark_history_readiness_requirement_exit_code_delta": 1
}
```

这里的关键语义是：`benchmark_history_status` 可以仍为 `pass`，但 readiness requirement fail 会让 readiness panel 进入 warn，并让 comparison 计为 benchmark history regression。

## 运行流程

1. `build_release_readiness_dashboard()` 读取 release bundle 和 gate report。
2. `_benchmark_history_summary()` 从 gate 优先、bundle 兜底汇总 benchmark readiness requirement。
3. `_benchmark_history_panel_status()` 根据 requirement fail 或非零 exit code 把 benchmark panel 标记为 warn。
4. `build_release_readiness_comparison()` 读取多个 readiness dashboard。
5. `_delta_from_baseline()` 计算 requirement status changed 和 exit-code delta。
6. `_is_benchmark_history_regression()` 把 requirement fail 或 exit-code 上升计为 benchmark regression。

## 测试覆盖

- `test_build_release_readiness_dashboard_ready`
  - 验证默认 pass requirement 不影响 ready dashboard。

- `test_build_release_readiness_reviews_benchmark_requirement_failure`
  - 构造 `benchmark_history_status=pass` 但 requirement fail 的 dashboard。
  - 验证 summary 保留失败原因，benchmark panel 变成 warn。

- `test_build_release_readiness_comparison_flags_benchmark_requirement_regression`
  - baseline requirement pass，current requirement fail。
  - 验证 comparison 的 benchmark regression count 为 1，且 delta 记录 status changed 与 exit-code delta。

- `test_write_release_readiness_comparison_outputs`
  - 验证 CSV 和 delta CSV 写出新增 requirement 字段。

## 运行截图和证据

- `d/369/图片/01-release-readiness-requirement-comparison.png`
- `d/369/解释/说明.md`

截图显示 CI/coverage regression 都是 0，但 benchmark readiness requirement 从 pass 变成 fail，因此 readiness comparison 产生 benchmark regression。

## 一句话总结

v369 让 benchmark history readiness requirement 进入 release readiness 和 readiness comparison 层，避免发布准备态只看旧 benchmark status 而漏掉最新 requirement 失败。

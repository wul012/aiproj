# 382-v368 release gate benchmark readiness

## 本版目标和边界

v367 已经让 release bundle 在 stale audit pass 之外读取 benchmark history readiness requirement。v368 继续向发布门禁推进一层，让 release gate 自己也能看到这份 requirement，并在 requirement 失败时给出 `warn / needs-review`。

本版不修改模型、训练、benchmark 预算或 release readiness dashboard。它只处理 release gate 的 summary、benchmark gate helper、Markdown/HTML 报告、CLI stdout 和对应测试。

## 关键文件

- `src/minigpt/release_gate.py`
  - `_build_summary()` 从 release bundle summary 继续拷贝 benchmark readiness requirement 字段。
  - 新字段包括 status、exit code 和 failed reasons，供后续报告、CLI 和推荐语消费。

- `src/minigpt/release_gate_benchmark.py`
  - `benchmark_history_gate_detail()` 在门禁 detail 中展示 requirement status、exit code 和 failed reasons。
  - `_benchmark_history_summary_result()` 把 requirement `fail` 或非零 exit code 视为 `warn`。
  - `_failed_reasons()` 把失败原因列表压缩成稳定的逗号分隔文本，避免 report detail 丢掉机器可读原因。

- `src/minigpt/release_gate_artifacts.py`
  - Markdown summary 增加 benchmark history readiness、exit 和 reasons。
  - HTML stats 增加 `Bench readiness` 和 `Bench readiness exit`，让截图里可以直接看见门禁触发来源。

- `scripts/check_release_gate.py`
  - CLI stdout 输出 requirement status、exit code 和 failed reasons，便于 CI 日志或人工检查快速定位。

- `tests/test_release_gate.py`
  - 默认 bundle fixture 带 pass requirement，保证正常发布不被误降级。
  - 新增 requirement fail 测试，构造 `benchmark_history_status=pass` 但 requirement fail 的 bundle，证明 warn 不是由 summary status 触发。
  - 输出测试验证 Markdown/HTML 包含新增 readiness 字段。

## 核心数据结构

release bundle summary 输入：

```json
{
  "release_status": "release-ready",
  "audit_status": "pass",
  "benchmark_history_status": "pass",
  "benchmark_history_readiness_requirement_status": "fail",
  "benchmark_history_readiness_requirement_exit_code": 1,
  "benchmark_history_readiness_requirement_failed_reasons": ["insufficient_ready_entries"]
}
```

release gate summary 输出：

```json
{
  "gate_status": "warn",
  "decision": "needs-review",
  "benchmark_history_status": "pass",
  "benchmark_history_readiness_requirement_status": "fail",
  "benchmark_history_readiness_requirement_exit_code": 1,
  "benchmark_history_readiness_requirement_failed_reasons": ["insufficient_ready_entries"]
}
```

这里的核心语义是：benchmark history 本身可以是 `pass`，但它的 readiness requirement 仍可要求人工 review。release gate 不把它升级为 hard fail，因为现阶段 tiny smoke 仍是 plumbing evidence；但它也不会让 release 直接 approved。

## 运行流程

1. `check_release_gate.py` 读取 release bundle。
2. `build_release_gate()` 建立 policy、checks 和 summary。
3. `benchmark_history_gate_result()` 合并 audit check status、bundle summary status 和 readiness requirement。
4. requirement fail 或 exit code 非零时，benchmark history gate check 返回 `warn`。
5. `_build_summary()` 汇总为 `gate_status=warn` 和 `decision=needs-review`。
6. JSON、Markdown、HTML 和 CLI stdout 同步保留 requirement 诊断字段。

## 测试覆盖

- `test_build_release_gate_passes_ready_bundle`
  - 验证 pass requirement 的 release gate 仍通过。

- `test_build_release_gate_warns_for_benchmark_history_readiness_requirement_failure`
  - 验证 `benchmark_history_status=pass` 但 requirement fail 时，release gate 进入 warn。
  - 断言 summary 保留 status、exit code 和 failed reasons。
  - 断言 check detail 包含 `readiness_requirement=fail` 和失败原因。

- `test_write_release_gate_outputs`
  - 验证 Markdown/HTML 报告能显示新增 readiness 字段。

## 运行截图和证据

- `d/368/图片/01-release-gate-readiness-requirement-warning.png`
- `d/368/解释/说明.md`

截图中的 release、audit、coverage、benchmark history 均为通过状态，但 benchmark readiness requirement 是 fail，所以最终 gate 是 warn。

## 一句话总结

v368 让 benchmark history readiness requirement 进入 release gate 决策层，避免 release-ready bundle 在门禁阶段绕过最新 benchmark readiness 失败。

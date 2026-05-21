# v375 benchmark reason recovery signal 代码讲解

## 本版目标和边界

v375 的目标是把 v374 的 failed reason removed 从“可见字段”升级为“明确恢复信号”。也就是说，报告要能直接回答：

- 这次是否新增了 benchmark readiness 失败原因？
- 这次是否移除了旧失败原因？
- 这属于 `regressed`、`recovered`、`mixed` 还是 `stable`？

本版不新增治理链，不改变训练流程，不把 recovery 当作模型质量证明。它只增强 release-readiness 证据链对风险收敛的表达能力。

## 前置能力

v373 已经能检测 failed reason additions，并把新增失败原因作为 review 信号。

v374 已经把 failed reason removals 贯通到 registry、maturity summary 和 maturity narrative。

v375 在这个基础上新增 drift status：

```text
stable     -> 没有 failed-reason drift
regressed  -> 新增失败原因
recovered  -> 旧失败原因消失
mixed      -> 同时新增和移除
```

## 关键文件

### `src/minigpt/release_readiness_comparison.py`

comparison delta 现在先计算：

- `added_failed_reasons`
- `removed_failed_reasons`

然后通过 `_reason_drift_status(...)` 得到：

```text
benchmark_history_readiness_requirement_failed_reason_drift_status
```

summary 新增：

- `benchmark_history_readiness_requirement_failed_reason_recovery_delta_count`
- `benchmark_history_readiness_requirement_failed_reason_drift_status_counts`

recommendations 也会在 recovered-only 情况下提示保留 recovery evidence。

### `src/minigpt/release_readiness_comparison_artifacts.py`

Markdown、HTML 和 CSV 输出新增 failed reason drift status。这样人工看报告时，不必自己比较 added/removed 数量。

### `src/minigpt/registry_release_readiness.py`

registry 聚合层读取 comparison 写出的 drift status。如果旧报告没有该字段，则根据 added/removed reason 列表派生。

registry summary 新增：

- recovery delta count
- drift status counts

这让多 run registry 能看到“多少个对比是恢复型变化”。

### `src/minigpt/maturity.py`

maturity summary 消费 registry 的 recovery 统计，但不会因为 recovered-only 降级。新增推荐语强调：recovery 是稳定性信号，不是模型质量证明。

### `src/minigpt/maturity_narrative_summary.py`

narrative summary 将 recovery delta count 和 drift status counts 带入 portfolio summary。

新增推荐语用于提醒：保留 recovery evidence，但不要把它和模型能力提升混为一谈。

### `src/minigpt/maturity_narrative_sections.py`

release quality claim 现在会直接写出：

```text
benchmark failed reasons added=N (...), removed=N (...), recovery deltas=N
```

### CLI 脚本

以下脚本新增 recovery diagnostics 输出：

- `scripts/register_runs.py`
- `scripts/build_maturity_summary.py`
- `scripts/build_maturity_narrative.py`

这些字段让 shell-only/CI 日志也能看到 recovery signal。

## 输入输出

输入仍然是 release readiness comparison 的 JSON 报告。

输出新增或增强字段：

- delta 行：`benchmark_history_readiness_requirement_failed_reason_drift_status`
- summary：`benchmark_history_readiness_requirement_failed_reason_recovery_delta_count`
- summary：`benchmark_history_readiness_requirement_failed_reason_drift_status_counts`

这些字段是正式证据，可以被 registry、maturity summary、maturity narrative 和 CLI 消费。

## 测试覆盖

本版更新了这些测试：

- `tests/test_release_readiness_comparison.py`
  - 验证 removed-only 是 `recovered`。
  - 验证 recovery delta count/status counts。
  - 验证 recommendations 提示保留 recovery evidence。
- `tests/test_registry.py`
  - 验证 registry summary 汇总 recovered drift。
- `tests/test_maturity.py`
  - 验证 recovered-only 保持 `overall_status=pass`。
  - 验证 recovery diagnostics 进入 summary 和 recommendations。
- `tests/test_maturity_narrative.py`
  - 验证 portfolio 仍可 ready。
  - 验证 release section claim 和 recommendations 展示 recovery signal。

验证结果：

```text
57 passed
```

## 运行证据

运行证据归档在：

```text
d/375/图片/01-benchmark-reason-recovery-signal-evidence.png
d/375/解释/说明.md
```

截图由 Playwright MCP 生成，证明证据页可以真实浏览器渲染。

## 一句话总结

v375 让 MiniGPT 的 release-readiness 链路能够明确表达“失败原因被修复”的恢复信号，并把它贯通到 registry、maturity 和 narrative，而不把恢复信号误当作模型质量证明。

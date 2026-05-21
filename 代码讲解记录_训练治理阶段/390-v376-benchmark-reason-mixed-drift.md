# v376 benchmark reason mixed drift 代码讲解

## 本版目标和边界

v376 的目标是把 benchmark-history readiness failed-reason 的 `mixed` 漂移显式化。

v375 已经有四种 drift status：

```text
stable
regressed
recovered
mixed
```

但 v375 的重点是 recovery signal。`mixed` 只存在于单条 delta 上，下游 summary 和 narrative 没有把它作为独立计数。v376 补齐这个边界：如果同一次对比既移除旧失败原因、又新增新失败原因，系统要明确告诉 reviewer：这不是纯恢复，而是风险形态替换。

本版不新增治理链，不改变训练流程，不扩大模型能力声明，也不把 release governance evidence 当作模型质量证明。

## 前置能力

本版承接 v373-v375：

- v373 让 failed-reason additions 进入 comparison、registry、maturity 和 narrative。
- v374 让 failed-reason removals 保持可见，并把 removed-only 视为恢复/稳定证据。
- v375 引入 drift status 和 recovery count。

v376 专门补 `mixed`：

```text
baseline failed reasons: insufficient_ready_entries, legacy_fixture_gap
compared failed reasons: insufficient_ready_entries, tiny_smoke_only

added  : tiny_smoke_only
removed: legacy_fixture_gap
status : mixed
```

这个场景里旧问题少了一个，但新问题多了一个，所以不能归类为 `recovered`。

## 关键文件

### `src/minigpt/release_readiness_comparison.py`

summary 新增：

```text
benchmark_history_readiness_requirement_failed_reason_mixed_delta_count
```

这个字段统计所有 delta 中 drift status 为 `mixed` 的数量。

recommendation 逻辑也新增 mixed 优先分支：

```text
At least one readiness comparison shows mixed benchmark readiness failed-reason drift...
```

它的语义是：即使 removed reason 存在，只要同时出现 added reason，就必须 review。

### `src/minigpt/release_readiness_comparison_artifacts.py`

Markdown 和 HTML 统计区新增 mixed delta 展示。这样人工查看 comparison report 时，不需要只看 status counts 才能发现 mixed。

### `src/minigpt/registry_release_readiness.py`

registry 聚合层新增：

```text
benchmark_history_readiness_requirement_failed_reason_mixed_delta_count
```

并在 leaderboard 排序中把 mixed drift 当作需要优先关注的 benchmark signal。这样多 run registry 不会把 mixed reason drift 藏在普通 stable/panel-changed 行里。

### `src/minigpt/registry_data.py`

`RegisteredRun` 新增：

```text
release_readiness_benchmark_requirement_failed_reason_mixed_delta_count
```

这个 run-level 字段让 `registry.csv`、HTML run card 和搜索文本都能看到 mixed drift。它也兼容旧 comparison JSON：如果旧报告没有 drift status，就根据 baseline/compared failed reasons 推导。

### `src/minigpt/maturity.py`

maturity summary 现在会把 registry 中的 mixed drift 带入：

```text
release_readiness_benchmark_requirement_failed_reason_mixed_delta_count
```

`_release_readiness_trend_status(...)` 会把 mixed drift 归为 `benchmark-regressed`。这和 recovered-only 不同：removed-only 可以保持稳定，mixed 必须 review。

### `src/minigpt/maturity_narrative_summary.py`

narrative summary 同步消费 mixed count，并在 portfolio status 中把 mixed drift 当作 review 条件。

recommendations 明确写出：

```text
removals do not cancel newly added reasons
```

这句话是本版的关键边界：mixed 不是 recovery。

### `src/minigpt/maturity_narrative_sections.py`

release quality claim 新增：

```text
mixed deltas=N
```

这样最终给人的 portfolio narrative 不只看到 added/removed/recovery，还能看到“风险替换”。

### CLI 脚本

以下脚本新增 mixed diagnostics：

- `scripts/compare_release_readiness.py`
- `scripts/register_runs.py`
- `scripts/build_maturity_summary.py`
- `scripts/build_maturity_narrative.py`

这些输出用于 shell-only、CI 日志或截图证据。

## 输入输出

输入仍然是 release readiness comparison 的 JSON 或 registry/maturity 既有产物。

新增输出字段包括：

```text
benchmark_history_readiness_requirement_failed_reason_mixed_delta_count
release_readiness_benchmark_requirement_failed_reason_mixed_delta_count
release_readiness_benchmark_requirement_failed_reason_drift_status_counts
```

这些字段是正式证据字段，可以被 registry、maturity summary、maturity narrative、Markdown/HTML/CSV 和 CLI 消费。

## 测试覆盖

本版新增或更新了这些测试：

- `tests/test_release_readiness_comparison.py`
  - 构造 added+removed 同时存在的 mixed 场景。
  - 断言 mixed count 为 1、recovery count 为 0。
  - 断言 recommendation 提醒 mixed drift。
- `tests/test_registry.py`
  - 验证 run row 和 registry summary 都能读取/派生 mixed drift。
  - 验证 registry CSV 包含 mixed count 字段。
- `tests/test_maturity.py`
  - 验证 mixed drift 会把 maturity trend 拉到 `benchmark-regressed`。
  - 验证 overall status 降为 `warn`。
- `tests/test_maturity_narrative.py`
  - 验证 mixed drift 让 portfolio 进入 `review`。
  - 验证 release section claim 包含 `mixed deltas=1`。
- `tests/test_maturity_artifacts.py`
  - 验证 Markdown/HTML artifact 渲染 mixed 字段。

验证结果：

```text
61 passed
```

## 运行证据

运行证据归档在：

```text
d/376/图片/01-benchmark-reason-mixed-drift-evidence.png
d/376/解释/说明.md
```

截图页面说明了 baseline/compared failed reasons、added/removed reason、mixed count、recovery count 和 portfolio review 影响。

## 一句话总结

v376 让 MiniGPT 的 release-readiness 链路能识别“旧失败原因消失但新失败原因出现”的风险替换场景，并把它作为正式 review 信号贯通到 registry、maturity、narrative、CLI 和报告产物。

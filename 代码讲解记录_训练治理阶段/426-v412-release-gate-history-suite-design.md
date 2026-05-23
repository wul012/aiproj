# v412 release gate benchmark history suite design

## 本版目标和边界

v412 的目标是把 v411 进入 release bundle 的 benchmark-history suite-design readiness 继续接到 release gate。这样 gate 不只判断 release status、audit score、artifact 完整度和 benchmark readiness requirement，也能直接看到 prompt suite design 是否还不适合比较。

本版不新增治理链，不训练 checkpoint，不扩展 benchmark suite，也不改变 release gate profile。它只让已有 gate check 消费 suite-design history 字段，并把这些字段展示到 summary、Markdown/HTML 和 CLI stdout。

## 前置能力

本版承接：

- v408：benchmark history ledger 保存 suite-design not-ready 和 design-change 计数。
- v409：maturity narrative 消费这些字段。
- v410：project audit 消费这些字段。
- v411：release bundle 消费这些字段，并修正 stale audit summary 被新 benchmark history 覆盖的问题。

v412 位于 gate 层，负责在最终 approval 前保留这条 prompt-suite 设计边界。

## 关键文件

### `src/minigpt/release_gate_benchmark.py`

`benchmark_history_gate_detail()` 新增：

```text
suite_design_not_ready=<n>
design_comparison_changed=<n>
```

`_benchmark_history_summary_result()` 的 warning keys 增加：

```text
benchmark_history_suite_design_non_comparison_ready_entries
```

因此即使 `benchmark_history_status=pass`，只要 release bundle summary 暴露 suite-design not-ready entry，benchmark history gate check 也会变成 `warn`。

### `src/minigpt/release_gate.py`

gate summary 新增：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

这些字段直接来自 release bundle summary。gate 本身不重新解析 benchmark history 文件，保持 release bundle 作为发布证据输入的边界。

### `src/minigpt/release_gate_artifacts.py`

Markdown Summary 新增：

```text
Benchmark history suite-design not-ready
Benchmark history design changes
```

HTML stats 新增：

```text
Bench design review
Bench design changes
```

这些字段用于 release gate 审阅和截图，不是模型质量证明。

### `scripts/check_release_gate.py`

CLI stdout 新增：

```text
benchmark_history_suite_design_non_comparison_ready_entries
benchmark_history_design_comparison_changed_entries
```

自动化日志可以直接看到 gate 是否发现 suite-design history 边界。

### `tests/test_release_gate.py`

测试覆盖新增和更新：

- ready bundle 默认 suite-design 计数为 `0`。
- suite-design not-ready 会让 benchmark history gate check 进入 `warn`。
- gate detail 包含 `suite_design_not_ready=1` 和 `design_comparison_changed=1`。
- `exit_code_for_gate(gate)` 在 warn 下仍为 `0`，`fail_on_warn=True` 时为 `1`。
- Markdown/HTML 和 CLI stdout 都包含新增字段。

## 输入输出

输入仍是：

```text
release_bundle.json
```

输出新增字段：

```text
gate_report.json
  summary.benchmark_history_suite_design_non_comparison_ready_entries
  summary.benchmark_history_design_comparison_changed_entries

gate_report.md/html
  Benchmark history suite-design not-ready
  Bench design review

CLI stdout
  benchmark_history_suite_design_non_comparison_ready_entries
  benchmark_history_design_comparison_changed_entries
```

## 测试覆盖

定向验证命令：

```text
python -m pytest tests\test_release_gate.py -q
python -m py_compile src\minigpt\release_gate.py src\minigpt\release_gate_benchmark.py src\minigpt\release_gate_artifacts.py scripts\check_release_gate.py tests\test_release_gate.py
```

完整验证还包括全量 pytest、source encoding hygiene 和 `git diff --check`。

## 运行证据

运行截图与说明归档在：

```text
d/412/图片/01-release-gate-history-suite-design-evidence.png
d/412/解释/说明.md
d/412/解释/v412-release-gate-history-suite-design-evidence.html
```

## 一句话总结

v412 把 prompt suite design 不就绪推进到 release gate，让最终 gate approval 前也能明确提示 benchmark history 仍需要 review。

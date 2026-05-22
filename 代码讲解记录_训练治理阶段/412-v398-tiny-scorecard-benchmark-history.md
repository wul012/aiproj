# v398 tiny scorecard benchmark history 代码讲解

## 本版目标和边界

v398 的目标是把 tiny scorecard comparison smoke 从“比较 + 决策”继续接到 benchmark history ledger。这样一次最小 CPU smoke 可以同时证明：

```text
baseline tiny run
        |
candidate tiny run
        |
scorecard comparison
        |
scorecard decision
        |
benchmark history
```

本版不扩大模型，不改变训练参数默认值，不声称 tiny smoke 代表真实模型质量。新增的 history 明确使用 `evidence_kind=tiny-smoke`，所以 readiness requirement 会保留 `not_real_benchmark_evidence` 失败原因；当 ready entries 不足时，也会保留 `insufficient_ready_entries`。

## 前置能力

v317-v341 建立 tiny scorecard comparison smoke、decision smoke、summary checker、CI wrapper 和 plan digest。v343-v351 又建立 benchmark history 及其在 maturity、audit、release readiness、registry 中的消费链。

v398 连接这两段能力：

```text
tiny smoke chain
        +--> scorecard comparison
        +--> scorecard decision
        +--> v398 benchmark history artifact

benchmark history chain
        +--> readiness requirement
        +--> boundary: tiny-smoke is plumbing evidence
```

## 关键文件

### `scripts/run_tiny_scorecard_comparison_smoke.py`

脚本新增 `benchmark-history` 输出目录：

```text
<out-dir>/benchmark-history/
        benchmark_history.json
        benchmark_history.csv
        benchmark_history.md
        benchmark_history.html
```

`build_summary()` 现在先调用 `build_tiny_benchmark_history()`，再把 history artifact 写入 summary 和 artifact status。核心输入是：

```text
scorecard-comparison/benchmark_scorecard_comparison.json
scorecard-decision/benchmark_scorecard_decision.json
```

核心输出字段是：

```text
benchmark_history_dir
benchmark_history.entry_count
benchmark_history.ready_count
benchmark_history.model_quality_claim
benchmark_history.readiness_requirement_status
benchmark_history.readiness_requirement_decision
benchmark_history.readiness_requirement_exit_code
benchmark_history.readiness_requirement_failed_reasons
benchmark_history.outputs
```

`render_summary()` 也同步输出 line-oriented 字段，例如：

```text
history_entry_count=1
history_ready_count=0
history_model_quality_claim=not_claimed
history_readiness_requirement_status=fail
history_readiness_requirement_decision=stop
history_readiness_requirement_exit_code=1
history_readiness_requirement_failed_reasons=insufficient_ready_entries,not_real_benchmark_evidence
history_json=<out-dir>/benchmark-history/benchmark_history.json
```

这些字段给 CI 日志、人工检查和后续脚本提供稳定入口。

### `tests/test_tiny_scorecard_comparison_smoke.py`

测试覆盖两类路径：

- `render_summary()` 的纯文本输出，确保 history 字段不会从 CLI summary 中消失。
- 真实 tiny smoke 链路，确保 `benchmark_history.json/html` 被写出，summary 中保留 `not_claimed`、`fail`、`not_real_benchmark_evidence` 等边界字段。

其中 `history_readiness_requirement_failed_reasons` 同时允许出现：

```text
insufficient_ready_entries
not_real_benchmark_evidence
```

这不是失败，而是本版希望保留的边界证明：tiny smoke 只说明链路能跑通，不说明模型已具备发布级质量。

## 输入输出格式

输入仍然来自 tiny smoke 生成的 scorecard comparison 和 decision artifact。本版没有引入新 CLI 参数，避免扩大使用面。

输出新增四个 benchmark history artifact：

- JSON：后续机器消费入口。
- CSV：人工和表格检查入口。
- Markdown：文档和评审入口。
- HTML：截图和可视化证据入口。

它们是本次运行的最终证据，不是临时文件；运行截图则归档到 `d/398`。

## 运行流程

```text
scripts/run_tiny_scorecard_comparison_smoke.py
        |
        +--> baseline tiny standard benchmark smoke
        +--> candidate tiny standard benchmark smoke
        +--> scripts/compare_benchmark_scorecards.py
        +--> scripts/build_benchmark_scorecard_decision.py
        +--> build_tiny_benchmark_history()
                |
                +--> build_benchmark_history(evidence_kind="tiny-smoke")
                +--> write_benchmark_history_outputs()
        +--> write tiny_scorecard_comparison_smoke_summary.json/txt
        +--> optional summary checker sidecars
```

关键点是 `evidence_kind="tiny-smoke"`。它让后续 history 消费方看到真实 artifact，同时不会把 smoke 误判成正式 benchmark。

## 测试覆盖

本版定向验证：

```text
python -m py_compile scripts/run_tiny_scorecard_comparison_smoke.py tests/test_tiny_scorecard_comparison_smoke.py
python -m pytest tests/test_tiny_scorecard_comparison_smoke.py -q
```

收口验证会继续执行：

```text
python -m pytest -q
python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-v398
git diff --check
```

## 证据归档

运行截图和说明放在：

```text
d/398/图片
d/398/解释/说明.md
```

`d/398/解释/v398-tiny-scorecard-benchmark-history-evidence.html` 是给 Playwright MCP 截图的静态证据页。它展示本版新增的 benchmark history 输出、summary 字段和 tiny-smoke 边界。

## 一句话总结

v398 让 tiny scorecard smoke 从“能比较、能决策”推进到“能进入 benchmark history 账本”，同时保留 tiny-smoke 不是模型质量证明的边界。

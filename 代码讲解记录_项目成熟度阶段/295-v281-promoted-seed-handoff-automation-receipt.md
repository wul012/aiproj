# v281 promoted seed handoff automation receipt

## 本版目标和边界

v281 的目标是给 promoted seed handoff 增加轻量 automation receipt artifact。

v280 已经新增 `automation_summary`，让完整 handoff report 有了一个最终自动化出口。但完整 report 包含 summary、execution、plan report、artifact rows、recommendations 等大量上下文。CI 或外部脚本通常只需要几个字段：

- 最终是否继续。
- 用什么退出码。
- 阻塞来源是什么。
- 哪些 requirement 失败。
- handoff 执行状态是什么。

v281 把这些字段抽成 compact receipt，避免外部脚本为了一个 decision 去解析完整报告结构。

本版不改变 `automation_summary` 的决策规则，不新增 CLI 开关，不移除旧 artifact。receipt 是新增输出。

## 前置链路

相关前置版本：

- v278：新增 `automation_gate`。
- v279：gate 增加 decision、exit code 和 requirement counts。
- v280：新增顶层 `automation_summary`，合并 gate blocker 和 handoff execution blocker。
- v281：把最终自动化出口写成 compact receipt artifact。

这版属于自动化集成体验增强，不是模型能力增强。

## 新增 artifact

位置：`src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

`write_promoted_training_scale_seed_handoff_outputs()` 现在除了写：

```text
promoted_training_scale_seed_handoff.json
promoted_training_scale_seed_handoff.csv
promoted_training_scale_seed_handoff.md
promoted_training_scale_seed_handoff.html
```

还会写：

```text
promoted_training_scale_seed_handoff_automation_receipt.json
promoted_training_scale_seed_handoff_automation_receipt.txt
```

JSON receipt 面向程序读取，text receipt 面向 shell、日志和人工快速检查。

## Receipt 字段

`build_promoted_training_scale_seed_handoff_automation_receipt(report)` 输出：

- `schema_version`
  - receipt schema 版本。
- `receipt_type`
  - 固定为 `promoted_training_scale_seed_handoff_automation`。
- `generated_at`
  - 继承完整 report 时间。
- `seed_path`
  - seed 来源。
- `seed_status`
  - seed 状态。
- `handoff_status`
  - handoff 执行状态。
- `execute`
  - 是否实际执行 plan command。
- `returncode`
  - plan command return code。
- `plan_status`
  - plan report 是否存在。
- `plan_report_path`
  - plan report 路径。
- `next_batch_command_available`
  - 是否存在下一步 batch command。
- `automation_decision`
  - 来自 `automation_summary.decision`。
- `automation_exit_code`
  - 来自 `automation_summary.exit_code`。
- `automation_blocking_source`
  - 来自 `automation_summary.blocking_source`。
- `automation_detail`
  - 来自 `automation_summary.detail`。
- `gate_status`
  - 来自 `automation_gate.status`。
- `gate_decision`
  - 来自 `automation_gate.decision`。
- `gate_required`
  - 是否请求 strict gate。
- `gate_blocking_requirement_count`
  - gate 层阻塞 requirement 数。
- `failed_requirements`
  - 失败 requirement 名称。
- `passed_requirements`
  - 通过 requirement 名称。
- `clean_evidence_requirement_status`
  - clean evidence requirement 状态。
- `clean_batch_review_requirement_status`
  - clean batch-review requirement 状态。

这些字段是从完整 report 中抽取的最终证据，不是重新计算的第二套规则。

## Text Receipt

`render_promoted_training_scale_seed_handoff_automation_receipt_text(report)` 生成 key/value 文本，例如：

```text
receipt_type=promoted_training_scale_seed_handoff_automation
handoff_status=planned
automation_decision=stop
automation_exit_code=1
automation_blocking_source=automation_gate
failed_requirements=['clean_evidence', 'clean_batch_review']
```

它适合放进 CI 日志，或者被简单脚本按行读取。

## CLI 行为

位置：`scripts/execute_promoted_training_scale_seed.py`

CLI 现在额外打印：

```text
automation_receipt_json=...
automation_receipt_text=...
```

这样调用方不用从 `outputs={...}` JSON 字符串里再取路径。

## 测试覆盖

`tests/test_promoted_training_scale_seed_handoff.py` 覆盖：

- receipt helper 是 public re-export。
- receipt JSON 包含 final automation decision、exit code、blocking source、failed requirements。
- receipt text 包含 line-oriented decision 字段。
- CLI stdout 输出 receipt JSON/text 路径。
- `write_promoted_training_scale_seed_handoff_outputs()` 确实写入两个 receipt 文件。
- handoff execution failed 时，receipt 的 blocking source 是 `handoff_execution`。

这组测试保护的是 external automation consumption，而不是模型质量。

## 运行证据

运行截图和解释归档在 `c/281`。

验证覆盖：

- seed handoff focused tests。
- promoted comparison/decision/seed/seed handoff 相关链路 tests。
- full unittest。
- source encoding hygiene。
- smoke artifact。
- Playwright/Chrome HTML 截图。

## 一句话总结

v281 给 promoted seed handoff 增加 compact automation receipt，让 CI 和外部脚本能稳定读取最终自动化结论，而不必解析完整 handoff report。

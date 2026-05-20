# v289 promoted seed handoff embedded receipt check report

## 本版目标和边界

v289 的目标是把 v288 inline 生成的 embedded receipt-check 结果写回 promoted seed handoff 主报告，让一个主 JSON/CSV/Markdown/HTML 就能看到 automation decision、receipt-check 和 embedded sidecar integrity 三层状态。

v288 已经做到：

- 执行脚本可以通过 `--embedded-receipt-check-out-dir` 运行 embedded checker。
- embedded checker 会检查主报告里的 `receipt_check` 和引用的 receipt/check sidecar。
- checker JSON/text 会在 stop 决策退出前写出。

但 v288 的 embedded checker 结果仍主要存在于 sidecar 输出里。v289 补上主报告展示，让审计者不必打开多个文件才能判断第三层校验是否通过。

本版不改变 receipt schema，不改变 embedded checker 判定算法，不改变默认执行行为，也不把治理证据说成模型质量提升。

## 前置链路

相关前置版本：

- v281：写出 compact automation receipt JSON/text。
- v282：新增 receipt checker CLI。
- v284：执行脚本可 inline 运行 receipt checker。
- v285：receipt-check 结果进入主 handoff report。
- v286：主 handoff report 内嵌 receipt-check 可被独立复核。
- v287：复核扩展到 receipt/check sidecar 完整性。
- v288：执行脚本可 inline 运行 embedded receipt-check。
- v289：inline embedded receipt-check 结果进入主 handoff report。

这版属于证据链可读性和审计闭环增强。

## 关键修改文件

### `scripts/execute_promoted_training_scale_seed.py`

执行脚本在 `_write_embedded_receipt_check_outputs()` 返回后新增回填逻辑：

```python
report["embedded_receipt_check"] = embedded_receipt_check
report["embedded_receipt_check_outputs"] = embedded_outputs
outputs = write_promoted_training_scale_seed_handoff_outputs(report, out_dir)
```

语义：

- embedded checker 仍然只在显式传入 `--embedded-receipt-check-out-dir` 时运行。
- checker sidecar 先写出，主报告再重写一次，把 sidecar 路径和摘要写进去。
- stop 决策也会先完成这次重写，再根据 `automation_summary` 退出。

这保持了 v288 的执行顺序，同时让主报告成为最终审计入口。

### `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

新增两个读取 helper：

```python
_embedded_receipt_check(report)
_embedded_receipt_check_outputs(report)
```

新增 CSV 字段投影：

```text
embedded_receipt_check_status
embedded_receipt_check_decision
embedded_receipt_check_sidecar_status
embedded_receipt_check_receipt_path_exists
embedded_receipt_check_json_exists
embedded_receipt_check_text_exists
embedded_receipt_check_output_json
embedded_receipt_check_output_text
```

Markdown 顶部摘要新增 embedded receipt-check 行。

HTML 新增 `Embedded Receipt Check` 区块，展示：

- status / decision / exit code
- sidecar status
- issue count / issues
- receipt/check sidecar 路径与存在性
- embedded check JSON/text 输出路径

这些字段都是校验证据，不参与重新计算 handoff 决策。

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

测试扩展了执行入口场景：

- continue 场景确认主 JSON 存在 `embedded_receipt_check` 和 `embedded_receipt_check_outputs`。
- CSV 包含 `embedded_receipt_check_status` 和 `embedded_receipt_check_sidecar_status`。
- Markdown 包含 `Embedded receipt check status`。
- HTML 包含 `Embedded Receipt Check`。
- stop 场景确认退出前主报告也保留 embedded check 诊断。

这保护的是“同一次执行生成的第三层校验结果必须进入最终主报告”。

## 输入输出格式

典型命令：

```powershell
python scripts/execute_promoted_training_scale_seed.py runs/training-scale-workflow/promoted-seed --execute --out-dir runs/training-scale-workflow/promoted-seed-handoff --receipt-check-out-dir runs/training-scale-workflow/promoted-seed-handoff/receipt-check --embedded-receipt-check-out-dir runs/training-scale-workflow/promoted-seed-handoff/embedded-receipt-check
```

主 JSON 新增：

```json
{
  "embedded_receipt_check": {
    "status": "pass",
    "decision": "continue",
    "sidecar_status": "pass",
    "receipt_path_exists": true,
    "receipt_check_json_exists": true,
    "receipt_check_text_exists": true
  },
  "embedded_receipt_check_outputs": {
    "json": "runs/.../promoted_training_scale_seed_handoff_embedded_receipt_check.json",
    "text": "runs/.../promoted_training_scale_seed_handoff_embedded_receipt_check.txt"
  }
}
```

主 CSV、Markdown、HTML 同步展示这些摘要字段。

## 测试覆盖

本版验证包括：

- `tests.test_promoted_training_scale_seed_handoff_receipt`
- `tests.test_promoted_training_scale_seed_handoff`
- promoted comparison / decision / seed / handoff / receipt 相关链路测试
- full unittest
- source encoding hygiene
- inline embedded receipt-check report smoke
- Playwright/Chrome HTML 渲染截图
- 文档一致性检查

关键断言保护：

- embedded check sidecar 仍然存在且通过。
- 主 report 也包含同一份 embedded check 摘要。
- CSV/Markdown/HTML 不丢失新增字段。
- stop 决策不会跳过证据写入。

## 运行证据

运行截图和解释归档在 `c/289`。

关键截图：

- `01-focused-tests.png`
- `02-handoff-tests.png`
- `03-related-chain-tests.png`
- `04-full-unittest.png`
- `05-source-encoding.png`
- `06-inline-embedded-receipt-check-report-smoke.png`
- `07-promoted-seed-handoff-html.png`
- `08-docs-check.png`

## 一句话总结

v289 把 promoted seed handoff 的 embedded receipt-check 从“sidecar 证据”推进为“主报告可直接审计的三层校验摘要”。

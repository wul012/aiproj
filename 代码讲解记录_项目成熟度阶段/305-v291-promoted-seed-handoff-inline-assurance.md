# v291 promoted seed handoff inline assurance

## 本版目标和边界

v291 的目标是把 v290 的目录级 assurance checker 接回 promoted seed handoff 执行脚本，让一次命令即可完成主报告、receipt-check、embedded receipt-check、assurance 的生成与归档。

v290 已经提供独立 CLI：

```powershell
python scripts/check_promoted_seed_handoff_assurance.py runs/.../promoted-seed-handoff
```

但它仍需要执行后再单独跑一次。v291 让 `execute_promoted_training_scale_seed.py` 在同一次执行中可选运行 assurance，并把结果写回主 JSON/CSV/Markdown/HTML。

本版不改变 handoff 决策，不改变 receipt schema，不改变默认执行行为，也不把证据链治理说成模型质量提升。

## 前置链路

相关前置版本：

- v281：compact automation receipt。
- v282-v283：receipt checker 与 checker artifact 输出。
- v284-v285：inline receipt-check 并写回主报告。
- v286-v289：embedded receipt-check、sidecar integrity、inline embedded check、主报告展示。
- v290：目录级 assurance checker。
- v291：inline assurance 并回填主报告。

这版属于“把收口工具接回主执行入口”。

## 关键修改文件

### `scripts/execute_promoted_training_scale_seed.py`

新增参数：

```python
--assurance-out-dir
```

语义：

- 只有显式传入时才运行 assurance。
- 依赖 `--embedded-receipt-check-out-dir`，因为 assurance 要读取 embedded receipt-check sidecar。
- 如果缺少 embedded checker 参数，会明确报错。

新增 helper：

```python
_write_handoff_assurance_outputs(...)
_print_handoff_assurance(...)
```

执行顺序变为：

```text
build handoff report
  -> optional receipt check
  -> write handoff outputs
  -> optional receipt-check outputs
  -> optional embedded receipt-check outputs
  -> rewrite handoff report with embedded check
  -> optional handoff assurance outputs
  -> rewrite handoff report with assurance
  -> print diagnostics
  -> exit from automation / receipt / embedded / assurance status
```

这保证 stop 决策退出前也能保留 assurance 证据。

### `src/minigpt/promoted_training_scale_seed_handoff_artifacts.py`

新增读取 helper：

```python
_handoff_assurance(report)
_handoff_assurance_outputs(report)
```

主 CSV 新增字段：

```text
handoff_assurance_status
handoff_assurance_decision
handoff_assurance_embedded_receipt_check_status
handoff_assurance_embedded_receipt_check_sidecar_status
handoff_assurance_output_json_exists
handoff_assurance_output_text_exists
handoff_assurance_json
handoff_assurance_text
```

Markdown 顶部摘要新增 assurance 行。

HTML 新增 `Handoff Assurance` 区块，展示 status、decision、sidecar 状态、issue count 和输出路径。

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

新增三类执行入口测试：

- continue 场景确认 assurance JSON/text 写出，并嵌回主报告。
- stop 场景确认退出前也写出 assurance 并回填。
- 参数错误场景确认 `--assurance-out-dir` 不能绕过 embedded checker。

这些测试保护的是“一条执行命令能落成完整 receipt assurance 证据链”。

## 输入输出格式

典型命令：

```powershell
python scripts/execute_promoted_training_scale_seed.py runs/training-scale-workflow/promoted-seed --execute --out-dir runs/training-scale-workflow/promoted-seed-handoff --receipt-check-out-dir runs/training-scale-workflow/promoted-seed-handoff/receipt-check --embedded-receipt-check-out-dir runs/training-scale-workflow/promoted-seed-handoff/embedded-receipt-check --assurance-out-dir runs/training-scale-workflow/promoted-seed-handoff/assurance
```

主 JSON 新增：

```json
{
  "handoff_assurance": {
    "status": "pass",
    "decision": "continue",
    "embedded_receipt_check_status": "pass",
    "embedded_receipt_check_sidecar_status": "pass",
    "embedded_receipt_check_output_json_exists": true,
    "embedded_receipt_check_output_text_exists": true
  },
  "handoff_assurance_outputs": {
    "json": "runs/.../promoted_training_scale_seed_handoff_assurance.json",
    "text": "runs/.../promoted_training_scale_seed_handoff_assurance.txt"
  }
}
```

## 测试覆盖

本版验证包括：

- `tests.test_promoted_training_scale_seed_handoff_receipt`
- `tests.test_promoted_training_scale_seed_handoff`
- promoted comparison / decision / seed / handoff / receipt 相关链路测试
- full unittest
- source encoding hygiene
- inline assurance smoke
- Playwright/Chrome HTML 渲染截图
- 文档一致性检查

## 运行证据

运行截图和解释归档在 `c/291`。

关键截图：

- `01-focused-tests.png`
- `02-handoff-tests.png`
- `03-related-chain-tests.png`
- `04-full-unittest.png`
- `05-source-encoding.png`
- `06-inline-assurance-smoke.png`
- `07-promoted-seed-handoff-html.png`
- `08-main-report-assurance-fields.png`

## 一句话总结

v291 把 promoted seed handoff 的 assurance checker 从“独立复核工具”推进为“执行入口可直接归档和展示的一等证据”。

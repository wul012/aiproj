# v286 promoted seed handoff embedded receipt check

## 本版目标和边界

v286 的目标是校验 promoted seed handoff 主报告里嵌入的 `receipt_check` 是否可信。

v285 已经把 inline receipt-check 结果写回主 JSON/CSV/Markdown/HTML，解决了人工阅读时需要跳到 sidecar 的断点。但主报告一旦携带校验结果，就会出现新的问题：这个嵌入值是否仍然和当前 handoff report 可重算出的 automation receipt 一致？

v286 解决这个问题：新增一个 embedded receipt-check verifier，从主 handoff JSON 重新生成 automation receipt，再复用 receipt checker 计算期望结果，并和主报告里的 `receipt_check` 做字段级对比。

本版不改变 receipt schema，不改变 `execute_promoted_training_scale_seed.py` 的默认行为，不改变 automation decision，也不声称模型能力提升。

## 前置链路

相关前置版本：

- v281：写出 compact automation receipt JSON/text。
- v282：新增 receipt checker CLI。
- v283：checker 支持目录输入和 check artifact 输出。
- v284：执行脚本可 inline 运行 checker。
- v285：inline checker 的结果进入主 handoff report。
- v286：主 handoff report 内嵌 checker 结果可被独立复核。

这版属于发布治理证据链的完整性增强。

## 关键修改文件

### `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`

本版在 receipt 模块里新增主报告解析和 embedded check 校验函数。

新增常量：

```python
HANDOFF_REPORT_FILENAME = "promoted_training_scale_seed_handoff.json"
EMBEDDED_RECEIPT_CHECK_JSON_FILENAME = "promoted_training_scale_seed_handoff_embedded_receipt_check.json"
EMBEDDED_RECEIPT_CHECK_TEXT_FILENAME = "promoted_training_scale_seed_handoff_embedded_receipt_check.txt"
```

这些常量把输入主报告和输出校验 artifact 的文件名固定下来，避免脚本和测试各自写字符串。

新增入口：

```python
load_promoted_training_scale_seed_handoff_report(path)
resolve_promoted_training_scale_seed_handoff_report_path(path)
check_promoted_training_scale_seed_handoff_embedded_receipt_check(report)
render_promoted_training_scale_seed_handoff_embedded_receipt_check(check)
write_promoted_training_scale_seed_handoff_embedded_receipt_check_outputs(check, out_dir)
```

`resolve_promoted_training_scale_seed_handoff_report_path()` 接受两类输入：

- 直接传 `promoted_training_scale_seed_handoff.json`。
- 传 handoff 输出目录，由函数自动定位主 JSON。

`check_promoted_training_scale_seed_handoff_embedded_receipt_check()` 是核心函数。它的流程是：

```text
read main handoff report
  -> extract report["receipt_check"]
  -> extract report["receipt_check_outputs"]
  -> rebuild automation receipt from the same report
  -> run normal receipt checker
  -> compare expected vs embedded fields
  -> return pass/fail plus diagnostics
```

对比字段包括：

- `status`
- `decision`
- `exit_code`
- `checker_exit_code`
- `blocking_source`
- `failed_requirements`
- `issue_count`
- `issues`

此外还会检查：

- `receipt_check` 必须存在。
- `receipt_check.receipt_path` 必须存在。
- `receipt_check_outputs.json` 和 `receipt_check_outputs.text` 必须存在。

这里检查的是主报告内部的结构一致性，不去打开 sidecar 文件本身。sidecar 文件内容已经由 v282-v283 的 receipt checker 覆盖；v286 关注的是主报告携带的字段是否和可重算结果一致。

### `scripts/check_promoted_seed_handoff_embedded_receipt.py`

新增 CLI：

```powershell
python scripts/check_promoted_seed_handoff_embedded_receipt.py runs/training-scale-workflow/promoted-seed-handoff --out-dir runs/training-scale-workflow/promoted-seed-handoff/embedded-receipt-check
```

输入可以是 handoff 输出目录，也可以是主 JSON。

输出会打印：

```text
embedded_receipt_check_status=pass
embedded_receipt_check_decision=continue
embedded_receipt_check_exit_code=0
embedded_receipt_check_checker_exit_code=0
embedded_receipt_check_issue_count=0
```

如果传 `--out-dir`，还会写出：

- `promoted_training_scale_seed_handoff_embedded_receipt_check.json`
- `promoted_training_scale_seed_handoff_embedded_receipt_check.txt`

退出语义和普通 receipt checker 保持一致：

- embedded check 本身失败：退出 1。
- embedded check 通过且 decision 是 `continue`：退出 0。
- embedded check 通过但 decision 是 `stop`：默认按 automation outcome 非零退出。
- 传 `--allow-stop` 时，结构一致的 `stop` 可以退出 0，适合只想检查证据结构的 CI 步骤。

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

本版扩展 receipt 测试：

- continue 场景：先用执行脚本生成带 `receipt_check` 的主报告，再用新 CLI 校验。
- tampered 场景：手动把主报告里的 `receipt_check.decision` 改成错误值，断言 embedded verifier 失败。
- stop 场景：构造 clean batch-review 阻塞，让主报告携带合法 stop receipt-check，断言默认非零、`--allow-stop` 通过。
- library 场景：直接调用 render/write 函数，确认 JSON/text 输出可被下游消费。

这些测试保护的是“主报告内嵌校验结果不能悄悄漂移”。

## 输入输出格式

输入主报告来自 v285 的 handoff 执行链：

```json
{
  "receipt_check": {
    "status": "pass",
    "decision": "continue",
    "exit_code": 0,
    "checker_exit_code": 0,
    "blocking_source": null,
    "failed_requirements": [],
    "issue_count": 0,
    "issues": [],
    "receipt_path": "..."
  },
  "receipt_check_outputs": {
    "json": "...",
    "text": "..."
  }
}
```

v286 输出的 embedded check JSON 记录：

```json
{
  "status": "pass",
  "decision": "continue",
  "receipt_path": "...",
  "receipt_check_json": "...",
  "receipt_check_text": "...",
  "issue_count": 0,
  "issues": []
}
```

这个输出不是新的 handoff 决策源，而是对主 handoff report 的一致性证明。

## 测试覆盖

本版验证包括：

- `tests.test_promoted_training_scale_seed_handoff_receipt`
- `tests.test_promoted_training_scale_seed_handoff`
- promoted comparison / decision / seed / handoff / receipt 相关链路测试
- full unittest
- source encoding hygiene
- embedded receipt-check smoke
- Playwright/Chrome HTML 渲染截图
- 文档一致性检查

## 运行证据

运行截图和解释归档在 `c/286`。

关键截图：

- `01-focused-tests.png`
- `02-handoff-tests.png`
- `03-related-chain-tests.png`
- `04-full-unittest.png`
- `05-source-encoding.png`
- `06-embedded-receipt-check-smoke.png`
- `07-promoted-seed-handoff-html.png`
- `08-docs-check.png`

## 一句话总结

v286 把 promoted seed handoff 主报告中的 receipt-check 从“写入可读”推进到“可重算复核”。

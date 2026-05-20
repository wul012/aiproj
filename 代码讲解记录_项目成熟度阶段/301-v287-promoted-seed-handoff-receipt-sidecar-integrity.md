# v287 promoted seed handoff receipt sidecar integrity

## 本版目标和边界

v287 的目标是让 promoted seed handoff 的 embedded receipt-check 不只校验主报告字段，还要校验主报告引用的 sidecar 文件是否真实存在、内容是否一致。

v286 已经做到：

- 从主 handoff JSON 重新生成 automation receipt。
- 复用 receipt checker 得到期望结果。
- 和主报告里的 `receipt_check` 做字段级对比。

但 v286 还有一个边界：它只确认主报告里的 `receipt_check` 可重算，没有真正打开 `receipt_check_outputs.json` 和 `receipt_check_outputs.text`。如果 sidecar 文件被删掉或被手改，v286 的主报告校验仍可能通过。v287 补上这个缺口。

本版不改变 receipt schema，不改变 handoff 执行脚本默认行为，不改变 automation decision，也不把治理证据误说成模型能力提升。

## 前置链路

相关前置版本：

- v281：写出 compact automation receipt JSON/text。
- v282：新增 receipt checker CLI。
- v283：checker 支持目录输入和 check artifact 输出。
- v284：执行脚本可 inline 运行 checker。
- v285：inline checker 的结果进入主 handoff report。
- v286：主 handoff report 内嵌 checker 结果可被独立复核。
- v287：主报告引用的 receipt/check JSON/text sidecar 文件也被校验。

这版属于证据链完整性和 CI 归档可靠性增强。

## 关键修改文件

### `src/minigpt/promoted_training_scale_seed_handoff_receipt.py`

`check_promoted_training_scale_seed_handoff_embedded_receipt_check()` 新增 `base_dir` 参数：

```python
def check_promoted_training_scale_seed_handoff_embedded_receipt_check(
    report: dict[str, Any],
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
```

`base_dir` 用于解析主报告里的相对路径。CLI 会传入 handoff report 所在目录，因此报告引用相对路径时也能被检查。

新增 sidecar 校验流程：

```text
extract receipt_check.receipt_path
extract receipt_check_outputs.json
extract receipt_check_outputs.text
resolve paths with base_dir
check file existence
load automation receipt JSON and rerun receipt checker
load receipt-check JSON and compare fields
load receipt-check text and compare rendered text
merge sidecar issues into embedded check issues
```

新增输出字段：

- `sidecar_status`
- `sidecar_issue_count`
- `sidecar_issues`
- `receipt_path_resolved`
- `receipt_path_exists`
- `receipt_check_json_resolved`
- `receipt_check_json_exists`
- `receipt_check_text_resolved`
- `receipt_check_text_exists`

这些字段让 CI 或人工 review 能直接看出是哪类 sidecar 断了。

### `scripts/check_promoted_seed_handoff_embedded_receipt.py`

CLI 保持命令名不变，但现在会把 `report_path.parent` 作为 `base_dir` 传入库函数：

```python
check = check_promoted_training_scale_seed_handoff_embedded_receipt_check(
    report,
    base_dir=report_path.parent,
)
```

输出新增：

```text
embedded_receipt_check_sidecar_status=pass
embedded_receipt_check_receipt_path_exists=True
embedded_receipt_check_json_exists=True
embedded_receipt_check_text_exists=True
```

默认退出语义保持不变：

- 校验失败：退出 1。
- `continue` 且校验通过：退出 0。
- `stop` 且校验通过：默认非零，`--allow-stop` 可放行。

### `tests/test_promoted_training_scale_seed_handoff_receipt.py`

新增三类 sidecar integrity 测试：

- check JSON sidecar 篡改：修改 `decision`，断言失败并出现 `receipt_check_outputs.json.decision`。
- check text sidecar 篡改：写入 `tampered=true`，断言失败并出现 text content mismatch。
- sidecar 缺失：删除 check JSON，断言 `receipt_check_json_exists == False` 且校验失败。

原有 continue 测试也新增断言：

- `sidecar_status == "pass"`
- receipt JSON 存在。
- check JSON 存在。
- check text 存在。

这些测试保护的是“主报告引用的 sidecar 不能过期、缺失或被手改”。

## 输入输出格式

输入仍是 v285/v286 的 handoff 主报告：

```json
{
  "receipt_check": {
    "status": "pass",
    "decision": "continue",
    "receipt_path": "..."
  },
  "receipt_check_outputs": {
    "json": "...",
    "text": "..."
  }
}
```

v287 校验输出新增 sidecar 字段：

```json
{
  "status": "pass",
  "sidecar_status": "pass",
  "receipt_path_exists": true,
  "receipt_check_json_exists": true,
  "receipt_check_text_exists": true,
  "sidecar_issues": []
}
```

这个输出仍然是验证证据，不是新的 handoff 决策源。

## 测试覆盖

本版验证包括：

- `tests.test_promoted_training_scale_seed_handoff_receipt`
- `tests.test_promoted_training_scale_seed_handoff`
- promoted comparison / decision / seed / handoff / receipt 相关链路测试
- full unittest
- source encoding hygiene
- sidecar integrity smoke
- Playwright/Chrome HTML 渲染截图
- 文档一致性检查

## 运行证据

运行截图和解释归档在 `c/287`。

关键截图：

- `01-focused-tests.png`
- `02-handoff-tests.png`
- `03-related-chain-tests.png`
- `04-full-unittest.png`
- `05-source-encoding.png`
- `06-sidecar-integrity-smoke.png`
- `07-promoted-seed-handoff-html.png`
- `08-docs-check.png`

## 一句话总结

v287 把 promoted seed handoff 的 receipt-check 证据从“主报告可复核”推进到“主报告和 sidecar 都能交叉验证”。

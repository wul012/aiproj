# v451 promoted receipt summary-check structured comparisons

## 本版目标和边界

v450 已经让 promoted seed handoff receipt contract summary 输出 `contract_checks`，让 summary 本体从自然语言 issues 进化为机器可读 contract artifact。v451 做下一层收口：让 contract summary-check 也输出结构化比较结果。

本版不改变 receipt schema，不改变 promoted seed handoff 执行逻辑，也不新增独立治理链。它只增强 summary-check 的可审计性：以前 summary-check 只把不一致写进 `issues` 字符串，现在它会明确列出每个 summary 字段和每个 sidecar 的比较结果。

## 前置链路

本版承接：

- v449：receipt contract summary 支持 schema-v4 boundary plan-check scopes。
- v450：receipt contract summary 支持 `contract_checks`。
- 既有 summary-check：已经能从 handoff report 重建 expected summary，并比较 JSON/text/Markdown/HTML sidecar。

v451 不扩展上游字段，只把比较动作本身结构化。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 新增 `summary_field_checks`，逐项记录 `SUMMARY_COMPARE_KEYS` 的 expected、actual、status。
  - 新增 `sidecar_checks`，逐项记录 text、Markdown、HTML 是否存在、是否匹配、expected/actual SHA-256。
  - Text 输出新增 summary field check count、failed count、sidecar check count、failed count。
  - Markdown 和 HTML 输出新增 `Summary Field Checks` 与 `Sidecar Checks` 表格。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 验证 pass 场景下 21 个 summary field checks 和 3 个 sidecar checks 都通过。
  - 验证篡改 schema、boundary scope、contract check 和 HTML sidecar 都会在结构化 check 中呈现失败。

## 核心数据结构

`summary_field_checks`：

```json
{
  "key": "receipt_schema_version",
  "status": "pass",
  "expected": 4,
  "actual": 4
}
```

字段语义：

- `key`
  - 被比较的 summary 字段名。
- `status`
  - `pass` 或 `fail`。
- `expected`
  - 从 handoff report 重建出的 expected summary 值。
- `actual`
  - 当前 summary JSON 中的实际值。

`sidecar_checks`：

```json
{
  "id": "html",
  "status": "pass",
  "exists": true,
  "expected_sha256": "...",
  "actual_sha256": "..."
}
```

字段语义：

- `id`
  - text、markdown 或 html。
- `status`
  - sidecar 内容是否与重建结果一致。
- `exists`
  - sidecar 文件是否存在。
- `expected_sha256` / `actual_sha256`
  - 预期内容和实际内容的摘要，便于日志和 CI 比较。

## 运行流程

1. Summary-check 读取实际 contract summary。
2. 如果能解析出 handoff path，就从 source handoff 重建 expected summary。
3. `_summary_field_checks()` 对 `SUMMARY_COMPARE_KEYS` 逐项生成比较 row。
4. `_sidecar_check()` 对 text、Markdown、HTML 生成 sidecar row，并记录 SHA-256。
5. `issues` 仍保留给人工读，但 JSON/text/Markdown/HTML 同时输出结构化 checks。
6. 如果 summary 字段、contract check、boundary scope 或 sidecar 被篡改，summary-check 会给出对应 fail row。

## 测试覆盖

Focused tests 共 `6 passed`：

- 正常 summary-check：字段比较和 sidecar 比较全部 pass。
- 篡改 `receipt_schema_version`：`summary_field_checks` 对应字段 fail。
- 篡改 `ci_boundary_plan_check_scopes`：字段比较 fail。
- 篡改 `contract_checks`：字段比较 fail。
- 篡改 HTML sidecar：`sidecar_checks` 中 html fail。
- CLI 输出仍写出 JSON/text/Markdown/HTML sidecar。

最终收口验证：

- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v451`
  - `784 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=351`，`clean_count=351`，`bom_count=0`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；仅有 Windows 工作区 LF/CRLF 换行提示，没有 whitespace error。

## 运行证据

`d/451` 保存了本版证据：

- `contract-summary/`：实际 contract summary。
- `contract-summary-check/`：新增结构化比较字段的 summary-check 输出。
- `contract_summary_check_stdout.txt`：CLI 输出中可见 `summary_field_checks` 和 `sidecar_checks`。
- `图片/01-receipt-summary-check-structured-fields.png`：Playwright MCP 截图，证明 HTML 展示结构化比较表。
- `解释/playwright_summary_check_structured_snapshot.md`：Playwright MCP 可访问性快照。

## 一句话总结

v451 把 promoted seed handoff receipt contract summary-check 从“失败时给 issue”推进到“每个字段和 sidecar 都有结构化比较结果”的自动化审计层。

# v450 promoted receipt contract checks

## 本版目标和边界

v449 已经把 promoted seed handoff receipt schema-v4 的 CI boundary plan-check scope 摊平成 contract summary。v450 继续做收口：把 contract summary 的判断结果整理成机器可读的 `contract_checks` 列表。

本版不新增训练能力，不改变 promoted seed handoff 的执行流程，不修改 receipt schema-v4，也不引入新的治理链。它解决的是自动化消费问题：之前 summary 有 `issues` 字符串，但机器想知道具体哪条 contract 失败，需要解析自然语言；现在可以直接读取 check row。

## 前置链路

本版承接：

- v448：automation receipt schema-v4，包含 boundary plan-check count。
- v449：receipt contract summary 展示 `schema_v4_ready` 和 `ci_boundary_plan_check_scopes`。

v450 只在 contract summary 层补充检查行，不回头修改上游 receipt、embedded check 或 handoff assurance 的字段名。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract.py`
  - 新增 `contract_checks`、`contract_check_count`、`failed_contract_check_count`。
  - Text 输出新增 `receipt_contract_checks=[...]`。
  - Markdown 和 HTML 输出新增 `Contract Checks` 表格。
  - `_contract_checks()` 把原本散落的 contract 判断整理成稳定 check row。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - Summary compare keys 增加 `contract_checks`、`contract_check_count`、`failed_contract_check_count`。
  - 如果 summary 里的 check row 被篡改，summary-check 会从 source handoff 重建 expected summary 并失败。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`
  - 验证 pass 场景下 `failed_contract_check_count=0`，并确认 `schema_v4_ready`、boundary check row 出现在 text/Markdown/HTML 中。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 验证篡改 `contract_checks` 会被 summary-check 拒绝。

## 核心数据结构

`contract_checks` 是本版核心结构：

```json
{
  "id": "schema_v4_ready",
  "scope": "receipt",
  "status": "pass",
  "expected": true,
  "actual": true,
  "detail": "receipt schema must support CI boundary plan-check contract"
}
```

字段语义：

- `id`
  - 稳定检查 ID，给 CI、脚本和后续审计用。
- `scope`
  - 检查所属范围，如 `receipt`、`assurance`、`handoff`。
- `status`
  - `pass` 或 `fail`。
- `expected` / `actual`
  - 机器可比对值，不需要解析文字。
- `detail`
  - 给人工审阅用的简短解释。

本版默认生成 10 条 check：

- `assurance_status_pass`
- `schema_v3_ready`
- `schema_v4_ready`
- `embedded_receipt_check_sidecar_pass`
- 3 条 suite-design count/name 一致性检查
- 3 条 CI boundary plan-check selected-within-handoff 检查

## 运行流程

1. Contract summary 读取 handoff assurance。
2. `_suite_design_scopes()` 和 `_ci_boundary_plan_check_scopes()` 先生成结构化 scope。
3. `_contract_checks()` 根据 assurance、suite scope、boundary scope 生成 check row。
4. Summary JSON/text/Markdown/HTML 都输出同一批 check row。
5. Contract summary check 从原 handoff 重新生成 expected summary。
6. 如果 `contract_checks`、check count 或 sidecar 内容被改动，summary-check 返回 fail。

## 测试覆盖

Focused tests 共 `10 passed`：

- `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`
  - 验证机器检查列表存在、失败数为 0，并渲染到 text/Markdown/HTML。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 验证篡改 `contract_checks` 后会被 summary-check 拒绝。

最终收口验证：

- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v450`
  - `784 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=351`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；只出现 Git 在 Windows 下的 LF/CRLF 工作区换行提示。

## 运行证据

`d/450` 保存了本版证据：

- `contract-summary/`：包含 `contract_checks` 的 contract summary。
- `contract-summary-check/`：重建 expected summary 后的 sidecar 一致性检查。
- `contract_summary_stdout.txt`：CLI 输出中的 `receipt_contract_checks=[...]`。
- `图片/01-receipt-contract-machine-checks.png`：Playwright MCP 截图，证明 HTML 中展示 `Contract Checks` 表。
- `解释/playwright_contract_checks_snapshot.md`：Playwright MCP 可访问性快照。

## 一句话总结

v450 把 promoted seed handoff receipt contract summary 从“可读报告”推进到“机器可消费的 contract check artifact”。

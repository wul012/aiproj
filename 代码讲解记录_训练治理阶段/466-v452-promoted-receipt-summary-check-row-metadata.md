# v452 promoted receipt summary-check row metadata

## 本版目标和边界

v451 已经把 promoted seed handoff receipt contract summary-check 的比较结果结构化为 `summary_field_checks` 和 `sidecar_checks`。v452 继续做一层小收口：让每个 check row 自带可机器消费的元数据。

本版不新增治理链，不改变 receipt schema，不改变 promoted seed handoff 的执行逻辑，也不改变 summary-check 的 pass/fail 决策。它只回答一个维护问题：后续消费这些 rows 时，能不能不靠字段名猜测，而是直接读取 `check_type`、`target`、`status_domain`、`required` 和 value kind。

## 前置链路

本版承接：

- v449：receipt contract summary 支持 schema-v4 boundary plan-check scopes。
- v450：receipt contract summary 支持 `contract_checks`。
- v451：receipt contract summary-check 支持结构化 summary field 与 sidecar comparisons。

v452 不扩展上游字段，只补齐比较 row 自身的契约描述。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check_rows.py`
  - 新增 summary field row、sidecar digest row、sidecar payload、stable value、digest、value kind 等 helper。
  - 每个 summary field row 统一生成 `id=summary_field.<key>`、`check_type=summary_field`、`target=summary.<key>`。
  - 每个 sidecar row 统一生成 `check_type=sidecar_digest`，并保留 expected/actual SHA-256。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 从 row helper 模块消费 `summary_field_checks()`、`summary_field_issues()`、`check_summary_sidecars()` 等函数。
  - Markdown 和 HTML 表格增加 `Type`、`Target`、`Detail` 列。
  - 主模块从 503 行降到 369 行，避免继续向一个文件堆 row 构造和渲染细节。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 验证 `contract_checks` summary row 的 `id`、`check_type`、`target`、`status_domain`、`required`、`expected_kind` 和 `actual_kind`。
  - 验证 HTML sidecar row 的 `check_type=sidecar_digest` 和 digest kind。
  - 保留 tamper 场景，确保 schema、boundary scope、contract check 和 HTML sidecar 篡改仍能失败。

## 核心数据结构

`summary_field_checks` row：

```json
{
  "id": "summary_field.contract_checks",
  "check_type": "summary_field",
  "target": "summary.contract_checks",
  "key": "contract_checks",
  "status": "pass",
  "status_domain": ["pass", "fail"],
  "required": true,
  "expected_kind": "list",
  "actual_kind": "list",
  "detail": "field matches rebuilt summary"
}
```

`sidecar_checks` row：

```json
{
  "id": "html",
  "check_type": "sidecar_digest",
  "target": "d/452/解释/contract-summary/promoted_training_scale_seed_handoff_receipt_contract_summary.html",
  "status": "pass",
  "status_domain": ["pass", "fail"],
  "required": true,
  "expected_kind": "sha256",
  "actual_kind": "sha256"
}
```

字段语义：

- `check_type`
  - `summary_field` 表示字段重建比较；`sidecar_digest` 表示 sidecar 内容摘要比较。
- `target`
  - 自动化系统可直接聚合的目标名称或路径。
- `status_domain`
  - 当前 row 的合法状态集合，方便下游做 schema-like 校验。
- `required`
  - 当前检查是否为必需项。v452 中所有现有 row 都是必需项。
- `expected_kind` / `actual_kind`
  - 记录比较值类型，帮助定位“内容不同”和“类型不同”的差异。
- `detail`
  - 人工读的简短解释，不参与判断。

## 运行流程

1. Summary-check 读取实际 contract summary。
2. 从 handoff report 重建 expected summary。
3. `summary_field_checks()` 对 `SUMMARY_COMPARE_KEYS` 逐项生成带元数据的 row。
4. `check_summary_sidecars()` 对 text、Markdown、HTML 生成 sidecar digest row。
5. 主模块聚合 counts、failed counts、issues，并写出 JSON/text/Markdown/HTML。
6. Markdown 和 HTML 不只显示 pass/fail，还显示 row type、target 和 detail。

## 测试覆盖

Focused tests 共 `6 passed`：

- 正常 summary-check：字段比较和 sidecar 比较全部 pass，且 row metadata 完整。
- 篡改 `receipt_schema_version`：对应 summary row fail，并保留 `detail=field differs from rebuilt summary`。
- 篡改 `ci_boundary_plan_check_scopes`：字段比较 fail。
- 篡改 `contract_checks`：字段比较 fail。
- 篡改 HTML sidecar：`sidecar_checks` 中 html fail，且 `check_type=sidecar_digest`。
- CLI 仍写出 JSON/text/Markdown/HTML sidecar。

最终收口验证：

- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v452`
  - `784 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=352`，`clean_count=352`，`bom_count=0`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；仅有 Windows 工作区 LF/CRLF 换行提示，没有 whitespace error。

## 运行证据

`d/452` 保存了本版证据：

- `contract-summary/`：实际 contract summary。
- `contract-summary-check/`：新增 row metadata 的 summary-check 输出。
- `contract_summary_check_stdout.txt`：CLI 输出中可见 `check_type`、`target`、`status_domain` 和 kind 字段。
- `图片/01-receipt-summary-check-row-metadata.png`：Playwright MCP 截图，证明 HTML 展示 row metadata。
- `解释/playwright_summary_check_row_metadata_snapshot.md`：Playwright MCP 可访问性快照。

## 一句话总结

v452 把 promoted seed handoff receipt contract summary-check 的比较 row 从“结构化结果”推进到“自描述结构化契约”，同时把 row 构造逻辑拆出主模块，降低后续维护压力。

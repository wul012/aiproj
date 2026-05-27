# v453 promoted receipt contract check row metadata

## 本版目标和边界

v452 让 promoted seed handoff receipt contract summary-check 的比较 rows 自描述。v453 把同样的结构化契约补到 contract summary 本体：`contract_checks` 不再只说明 check id、scope 和 pass/fail，还直接暴露 check type、target、状态域、是否必需和值类型。

本版不改变 receipt schema，不改变 promoted seed handoff 执行逻辑，不改变 contract summary 的 pass/fail 判断，也不新增治理链。它只增强已有 contract summary 的自动化可消费性，并把 row 构造逻辑从主模块拆出去。

## 前置链路

本版承接：

- v450：receipt contract summary 增加机器可读 `contract_checks`。
- v451：summary-check 增加结构化 summary field 与 sidecar comparisons。
- v452：summary-check rows 增加 row-level metadata。

v453 的位置更靠前：它让 contract summary 本体生成的 `contract_checks` 也具备相同的自描述能力。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_rows.py`
  - 新增 `build_contract_checks()`，集中构造 contract check rows。
  - 新增 `contract_check()`，统一补齐 `check_type`、`target`、`status_domain`、`required`、`expected_kind`、`actual_kind`。
  - 新增 `failed_contract_check_count()` 和 `contract_check_rows()`，让主模块只负责聚合和渲染。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract.py`
  - 使用新 helper 生成 `contract_checks`。
  - Markdown 和 HTML `Contract Checks` 表格新增 `Type`、`Target`、`Detail` 列。
  - 主模块从 517 行降到 450 行，避免 contract summary 渲染、聚合和 row 构造继续堆在一个文件。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`
  - 验证 `schema_v4_ready` row 的 `check_type=schema_readiness`、`target=receipt.schema_v4_ready`、状态域和值类型。
  - 验证 CI boundary plan-check row 的 target 出现在 Markdown。
  - 验证失败 row 仍保留 `status_domain=["pass", "fail"]`，且失败计数不变。

## 核心数据结构

`contract_checks` row：

```json
{
  "id": "schema_v4_ready",
  "check_type": "schema_readiness",
  "target": "receipt.schema_v4_ready",
  "scope": "receipt",
  "status": "pass",
  "status_domain": ["pass", "fail"],
  "required": true,
  "expected": true,
  "actual": true,
  "expected_kind": "bool",
  "actual_kind": "bool",
  "detail": "receipt schema must support CI boundary plan-check contract"
}
```

本版使用的 check type：

- `status_equals`
  - 用于 assurance status 和 embedded receipt-check sidecar status。
- `schema_readiness`
  - 用于 schema-v3、schema-v4 readiness。
- `count_consistency`
  - 用于 suite-design regression count 与 name count 一致性。
- `selected_within_handoff`
  - 用于 CI boundary plan-check selected count 不超过 handoff count。

## 运行流程

1. Contract summary 从 promoted seed handoff assurance 读取 receipt、sidecar、suite-design、boundary plan-check 证据。
2. `_suite_design_scopes()` 和 `_ci_boundary_plan_check_scopes()` 继续生成聚合 scopes。
3. `build_contract_checks()` 生成带 metadata 的 contract rows。
4. `failed_contract_check_count()` 计算失败数量。
5. Text 输出继续保留 `receipt_contract_checks=<json>`。
6. Markdown 和 HTML 把 `check_type`、`target` 和 `detail` 展示给人工审阅。
7. Summary-check 会重新构造 expected summary 并比较 `contract_checks`，证明新 metadata 可被重建和 sidecar 验证。

## 测试覆盖

Focused tests 共 `10 passed`：

- Contract summary 正常路径：schema-v4 check row metadata 完整。
- Boundary plan-check 路径：Markdown 暴露 `ci_boundary_plan_check.handoff.selected_within_handoff` target。
- 篡改 suite-design sidecar：contract summary 仍失败，失败 row 保留状态域。
- Contract summary CLI：继续写出 JSON/text/Markdown/HTML。
- Summary-check tests：继续验证 summary field rows、sidecar rows、tamper 场景和 CLI sidecars。

最终收口验证：

- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v453`
  - `784 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=353`，`clean_count=353`，`bom_count=0`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；仅有 Windows 工作区 LF/CRLF 换行提示，没有 whitespace error。

## 运行证据

`d/453` 保存了本版证据：

- `contract-summary/`：带 row metadata 的 contract summary。
- `contract-summary-check/`：对 v453 contract summary 的重建式 summary-check。
- `contract_summary_stdout.txt`：CLI 输出中可见 contract check metadata。
- `图片/01-contract-summary-check-row-metadata.png`：Playwright MCP 截图，证明 HTML 展示 metadata。
- `解释/playwright_contract_check_row_metadata_snapshot.md`：Playwright MCP 可访问性快照。

## 一句话总结

v453 把 promoted seed handoff receipt contract summary 的 contract checks 从“机器可读检查列表”推进到“自描述检查契约”，并把 row 构造从主模块拆出，降低后续维护压力。

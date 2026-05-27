# v454 promoted receipt contract check type summary

## 本版目标和边界

v453 让 promoted seed handoff receipt contract summary 的 `contract_checks` 具备 row-level metadata。v454 继续做同一条链路的收口：给这些 rows 增加顶层聚合 profile，让报告直接暴露每类检查的数量、通过数、失败数、required 数和 target 列表。

本版不改变 receipt schema，不改变 promoted seed handoff 执行逻辑，不改变 contract summary 的 pass/fail 判断，也不新增治理链。它只把既有明细 rows 汇总成更易消费的 profile，并顺手拆出 context helper，避免主模块继续变大。

## 前置链路

本版承接：

- v450：receipt contract summary 增加机器可读 `contract_checks`。
- v453：`contract_checks` 增加 `check_type`、`target`、状态域和 value kind。

v454 使用这些 metadata 生成聚合，不引入新的判断来源。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_rows.py`
  - 新增 `contract_check_status_counts()`。
  - 新增 `contract_check_type_summary()`，按 `check_type` 汇总 count、passed、failed、required 和 targets。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_context.py`
  - 抽出 suite-design scopes、CI boundary plan-check scopes、contract issues、row list 和 int helper。
  - 让主 contract summary 模块从 513 行降到 394 行。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract.py`
  - summary 顶层新增 `contract_check_status_counts` 和 `contract_check_type_summary`。
  - text 输出新增 `receipt_contract_check_status_counts` 与 `receipt_contract_check_type_summary`。
  - Markdown 和 HTML 新增 `Contract Check Type Summary` 表格。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - `SUMMARY_COMPARE_KEYS` 纳入新增的两个 summary 字段，保证 summary-check 会验证 profile 是否可重建。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract.py`
  - 验证状态计数、四类 check type 的聚合数量和 target。
  - 验证失败场景下 type profile 会把 `status_equals` 标记为失败。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 验证 summary-check field rows 包含 `contract_check_type_summary`。

## 核心数据结构

`contract_check_status_counts`：

```json
{
  "pass": 10,
  "fail": 0
}
```

`contract_check_type_summary` row：

```json
{
  "check_type": "schema_readiness",
  "status": "pass",
  "status_domain": ["pass", "fail"],
  "count": 2,
  "passed_count": 2,
  "failed_count": 0,
  "required_count": 2,
  "targets": ["receipt.schema_v3_ready", "receipt.schema_v4_ready"],
  "target_count": 2
}
```

字段语义：

- `check_type`
  - 聚合维度，来自 v453 的 row metadata。
- `status`
  - 该类型下只要存在失败 row 就是 `fail`，否则为 `pass`。
- `count` / `passed_count` / `failed_count`
  - 该类型下的总数、通过数和失败数。
- `required_count`
  - 该类型下必需检查数量。
- `targets`
  - 该类型覆盖的目标字段或证据边界。

## 运行流程

1. Contract summary 从 assurance 读取 receipt、sidecar、suite-design、boundary plan-check 证据。
2. `build_contract_checks()` 生成 v453 的自描述 check rows。
3. `contract_check_status_counts()` 汇总 pass/fail。
4. `contract_check_type_summary()` 按 `check_type` 汇总 counts 和 targets。
5. Text、Markdown、HTML 输出都展示 profile。
6. Summary-check 从 handoff 重建 expected summary，并比较 profile 字段，防止 profile 与明细 rows 不一致。

## 测试覆盖

Focused tests 共 `10 passed`：

- Contract summary 正常路径：状态计数为 `{"pass": 10, "fail": 0}`。
- Contract type profile：验证 `schema_readiness`、`status_equals`、`count_consistency`、`selected_within_handoff` 数量。
- Boundary plan-check 路径：继续验证 target 出现在报告。
- 篡改 suite-design sidecar：失败 type profile 会标记对应类型。
- Summary-check：验证新增 profile 字段进入 field comparison。

最终收口验证：

- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v454`
  - `784 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=354`，`clean_count=354`，`bom_count=0`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；仅有 Windows 工作区 LF/CRLF 换行提示，没有 whitespace error。

## 运行证据

`d/454` 保存了本版证据：

- `contract-summary/`：带 check type summary 的 contract summary。
- `contract-summary-check/`：对 v454 contract summary 的重建式 summary-check。
- `contract_summary_stdout.txt`：CLI 输出中可见 status counts 和 type summary。
- `图片/01-contract-check-type-summary.png`：Playwright MCP 截图，证明 HTML 展示 type profile。
- `解释/playwright_contract_check_type_summary_snapshot.md`：Playwright MCP 可访问性快照。

## 一句话总结

v454 把 promoted seed handoff receipt contract summary 从“自描述检查明细”推进到“明细 + 聚合 profile”并存，让自动化消费和人工审阅都能更快定位检查类型层面的风险。

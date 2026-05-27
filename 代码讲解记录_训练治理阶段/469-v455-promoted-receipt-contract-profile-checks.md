# v455 promoted receipt contract profile checks

## 本版目标和边界

v454 给 promoted seed handoff receipt contract summary 增加了 `contract_check_status_counts` 和 `contract_check_type_summary`。v455 继续收口同一条链路：让 summary-check 不只比较“actual 与 rebuilt expected 是否相同”，还要验证 actual summary 内部的聚合 profile 是否真的能从 `contract_checks` 明细重新推导出来。

本版不改变 receipt schema，不改变 promoted seed handoff、assurance smoke 或 contract summary 的生成语义，也不新增治理链。它只给 v454 的聚合字段补一层内部一致性检查，防止明细 rows 和聚合 profile 脱节。

## 前置链路

本版承接：

- v450：contract summary 增加机器可读 `contract_checks`。
- v453：`contract_checks` 增加 `check_type`、`target`、状态域和 value kind。
- v454：summary 顶层增加 status/type aggregate profile。

v455 使用同一批 `contract_checks` 重新计算聚合，不引入额外判断来源。

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check_rows.py`
  - 新增 `contract_profile_checks()`，从 actual summary 的 `contract_checks` 反推四个聚合字段。
  - 新增 `contract_profile_check()`，生成统一的 `contract_profile_consistency` row。
  - 新增 `contract_profile_issues()`，把失败 row 转成 summary-check issue。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - Summary-check 执行时先生成 contract profile checks，再执行 expected rebuild 和 sidecar digest 检查。
  - JSON 输出新增 `contract_profile_status`、`contract_profile_check_count`、`failed_contract_profile_check_count`、`contract_profile_checks`。
  - Text、Markdown、HTML 输出新增 profile 状态和 `Contract Profile Checks` 表格。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 正常路径验证 4 个 profile checks 全部 pass。
  - 篡改 `contract_check_type_summary` 后，summary-check 会因 profile 脱节失败。

## 核心数据结构

`contract_profile_consistency` row 示例：

```json
{
  "id": "contract_profile.contract_check_type_summary",
  "check_type": "contract_profile_consistency",
  "target": "summary.contract_check_type_summary",
  "key": "contract_check_type_summary",
  "status": "pass",
  "status_domain": ["pass", "fail"],
  "required": true,
  "expected_kind": "list",
  "actual_kind": "list"
}
```

字段语义：

- `expected`
  - 从 actual summary 的 `contract_checks` 明细 rows 重新计算得到。
- `actual`
  - actual summary 顶层已有的聚合字段。
- `target`
  - 被验证的 summary 字段，例如 `summary.contract_check_type_summary`。
- `status`
  - `expected` 与 `actual` 稳定化后完全一致才是 `pass`。

## 运行流程

1. Summary-check 读取 actual contract summary JSON。
2. `contract_profile_checks()` 取出 actual 的 `contract_checks`。
3. 重新计算：
   - `contract_check_count`
   - `failed_contract_check_count`
   - `contract_check_status_counts`
   - `contract_check_type_summary`
4. 将计算值与 actual summary 顶层 profile 字段比较。
5. 任一 profile 不一致时写入 `issues`，summary-check 总体 status 变为 `fail`。
6. 后续仍继续执行 handoff rebuild、summary field comparison 和 sidecar digest comparison。

## 测试覆盖

Focused tests 覆盖：

- 正常 contract summary-check：4 个 `contract_profile_consistency` row 全部通过。
- 文本输出包含 `receipt_contract_summary_check_failed_contract_profile_check_count=0`。
- Markdown 和 HTML 输出包含 `Contract Profile Checks` 表格。
- 篡改 `contract_check_type_summary[0].failed_count` 后，profile check 标记失败并写入 issue。
- 原有 summary field tamper、boundary scope tamper、contract check tamper、HTML sidecar tamper 仍然保留。

本版最终验证：

- `python -m py_compile` 新增/修改模块和测试文件。
- `python -m pytest tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py -q -o cache_dir=runs/pytest-cache-v455-focused`。
  - `7 passed`。
- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v455`。
  - `785 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`。
  - `status=pass`，`source_count=354`，`clean_count=354`，`bom_count=0`，`syntax_error_count=0`。
- `git diff --check`。
  - 通过；仅有 Windows 工作区 LF/CRLF 换行提示，没有 whitespace error。

## 运行证据

`d/455` 保存了本版证据：

- `解释/contract-summary/`：基于 v448 promoted handoff 重新生成的 receipt contract summary。
- `解释/contract-summary-check/`：包含 profile checks 的 summary-check JSON/text/Markdown/HTML。
- `解释/contract-summary-check-stdout.txt`：CLI 输出中可见 `contract_profile_status=pass` 和 `failed_contract_profile_check_count=0`。
- `图片/01-contract-profile-checks.png`：Playwright MCP 截图，证明 HTML 展示 `Contract Profile Checks`。
- `解释/playwright_contract_profile_checks_snapshot.md`：Playwright MCP 可访问性快照。

## 一句话总结

v455 把 promoted seed handoff receipt contract summary-check 从“能比较重建结果”推进到“还能验证 actual summary 内部 profile 是否自洽”，让 v454 的聚合字段真正具备可复核入口。

# v456 promoted receipt summary-check family summary

## 本版目标和边界

v455 让 receipt contract summary-check 能验证 actual summary 内部的 profile 是否由 `contract_checks` 明细推导出来。v456 不再继续扩展新的治理链，而是把现有 summary-check 的失败归因做成 compact rollup：一眼看出失败来自 summary field、contract profile，还是 sidecar digest。

本版不改变 promoted seed handoff 语义，不改变 receipt contract summary 生成逻辑，也不改变 pass/fail 判断来源。它只给 summary-check 输出增加更好消费的 failure family summary 和 failed target list。

## 前置链路

本版承接：

- v451：summary-check 增加 structured field/sidecar checks。
- v455：summary-check 增加 contract profile consistency checks。

v456 把这三类检查归一到同一个 triage 视图：

- `summary_field_checks`
- `contract_profile_checks`
- `sidecar_checks`

## 关键文件

- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check_rows.py`
  - 新增 `summary_check_family_summary()`。
  - 新增 `summary_check_failed_targets()`。
  - 新增 family row 和 failed target row 的小 helper。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check_render_sections.py`
  - 新增小型渲染 section 模块。
  - 负责 text、Markdown、HTML 中的 family summary 和 failed target 展示，避免主模块继续膨胀。
- `src/minigpt/promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 接入 `check_family_summary`、`failed_check_target_count`、`failed_check_targets`。
  - 报告首屏新增 `Failed Targets` 指标。
- `tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py`
  - 验证正常路径三类 family 全部 pass。
  - 验证 summary field 篡改、contract profile 篡改、sidecar 篡改会落入正确 family。

## 核心数据结构

`check_family_summary` row 示例：

```json
{
  "family": "contract_profile",
  "check_type": "summary_check_family",
  "target": "summary.contract_profile_checks",
  "status": "pass",
  "check_count": 4,
  "passed_count": 4,
  "failed_count": 0,
  "required_failed_count": 0,
  "failed_targets": []
}
```

`failed_check_targets` row 示例：

```json
{
  "family": "contract_profile",
  "id": "contract_profile.contract_check_type_summary",
  "check_type": "contract_profile_consistency",
  "target": "summary.contract_check_type_summary",
  "status": "fail",
  "required": true,
  "detail": "contract check type summary must be derived from the embedded contract check rows; aggregate differs from rows"
}
```

字段语义：

- `family`
  - 失败归属：summary field、contract profile 或 sidecar。
- `failed_targets`
  - 去重后的失败目标，供人快速定位。
- `failed_check_targets`
  - 逐条失败检查明细，供 CI 或后续报告消费。
- `required_failed_count`
  - required check 的失败数量，避免只看总数时漏掉强约束。

## 运行流程

1. Summary-check 先生成 summary field checks。
2. 再生成 contract profile checks。
3. 再生成 sidecar digest checks。
4. `summary_check_family_summary()` 对三类 rows 进行聚合。
5. `summary_check_failed_targets()` 抽出所有失败目标。
6. JSON/text/Markdown/HTML 都输出同一组 family summary 和 failed targets。

## 测试覆盖

Focused tests：

- 正常路径：`summary_field`、`contract_profile`、`sidecar` family 均为 `pass`。
- 正常路径：`failed_check_target_count=0`。
- 篡改 `receipt_schema_version`：`summary_field` family 变为 `fail`，失败 target 包含 `summary.receipt_schema_version`。
- 篡改 `contract_check_type_summary`：`contract_profile` family 变为 `fail`，失败 target 包含 `summary.contract_check_type_summary`。
- 篡改 HTML sidecar：`sidecar` family 变为 `fail`，失败 target 指向 contract summary HTML。

本版最终验证：

- `python -m py_compile` 覆盖新增模块、修改模块和测试文件。
- `python -m pytest tests/test_promoted_training_scale_seed_handoff_receipt_contract_check.py -q -o cache_dir=runs/pytest-cache-v456-focused`
  - `7 passed`。
- `python -m pytest tests -q -o cache_dir=runs/pytest-cache-v456`
  - `785 passed`。
- `python -B scripts/check_source_encoding.py --out-dir runs/source-encoding-hygiene-local`
  - `status=pass`，`source_count=355`，`clean_count=355`，`bom_count=0`，`syntax_error_count=0`。
- `git diff --check`
  - 通过；仅有 Windows 工作区 LF/CRLF 换行提示，没有 whitespace error。

## 运行证据

`d/456` 保存本版证据：

- `解释/contract-summary/`：用于复核的 receipt contract summary。
- `解释/contract-summary-check/`：包含 `check_family_summary` 和 `failed_check_targets` 的 summary-check 输出。
- `解释/contract-summary-check-stdout.txt`：CLI 输出中可见 `failed_check_target_count=0`。
- `图片/01-check-family-summary.png`：Playwright MCP 截图，证明 HTML 展示 family summary。
- `解释/playwright_check_family_summary_snapshot.md`：Playwright MCP 可访问性快照。

## 一句话总结

v456 让 receipt contract summary-check 从“列出所有检查”推进到“能快速归因失败属于哪类检查”，提升 CI 读取和人工排障效率。

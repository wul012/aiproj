# v1088 publication receipt contract check

## 本版目标

v1088 的目标是对 v1087 receipt 做 contract check：读取 v1087 receipt 里保存的 v1086 source review 路径，重新调用 v1087 builder，生成一份 rebuilt receipt，再和原始 receipt 做字段级比对。

本版不做的事：

- 不训练模型
- 不修改 v1087 receipt
- 不接受 candidate
- 不打开 production promotion
- 不把治理证据解释成模型质量提升

## 路线来源

v1087 已经把 v1086 review 记录为 downstream lookup-only receipt。v1088 接在 receipt 后面，承担“重建和防篡改”的角色。它对应的是 v1084 的 contract-check 模式，只是源头从 v1082/v1083 升级到 v1086/v1087。

这条路线的价值是让 receipt artifact 不只是一个静态 JSON，而是可以从上游 review 再次推导出来。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1088.py`
  - 核心 contract-check builder。
  - 定位 source review，重建 receipt，比对 summary、receipt、consumer receipts 和 source digest。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1088_artifacts.py`
  - 输出 JSON/CSV/TXT/MD/HTML。
  - HTML 用于截图和人工检查，CSV 用于逐项审计。

- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1088.py`
  - CLI 入口。
  - 接收 v1087 receipt 目录或 JSON 文件，并支持 `--require-pass`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1088.py`
  - 覆盖正常重建、granted use 篡改、source review 缺失、source digest 篡改和 CLI 失败退出。

- `e/1088/解释/receipt-check-v1088/`
  - 真实运行输出目录。
  - 下一版 index 应消费 v1087 receipt 和 v1088 check。

## 核心数据结构

contract check 结果包含：

- `original_summary` 和 `rebuilt_summary`
  - 对比 receipt readiness、receipt status、consumer name、granted use、lookup key count、promotion boundary 和 next step。

- `original_receipt` 和 `rebuilt_receipt`
  - 对比 receipt 主体字段，包括 source review path、source review digest、source receipt/index/check 路径、review status 和 model quality claim。

- `check_rows`
  - 包含 46 项检查。
  - 前置检查覆盖 source review 是否存在、status/decision/failed_count/digest 是否一致。
  - 后续字段检查覆盖 summary 和 receipt 每个关键字段。

- `summary`
  - 汇总 original/rebuilt status、use、lookup count、promotion boundary 和下一步 index 路由。

## 核心流程

1. CLI 定位 v1087 receipt JSON。
2. builder 读取原始 receipt 的 summary 和 receipt body。
3. `_resolve_source_review_path` 找到 receipt 内的 v1086 review 路径。
4. `_rebuild_receipt` 使用 v1087 builder 从 v1086 review 重建 receipt。
5. `_checks` 比对 status、decision、failed_count、digest、consumer receipts、summary fields 和 receipt fields。
6. artifact writer 输出多格式 sidecar。

## 测试覆盖

- 合法 receipt 可以通过，保护正常 contract check。
- 篡改 `granted_use` 会失败，保护 lookup-only 边界。
- 删除 source review 会失败，保护上游路径可追踪。
- 篡改 source digest 会失败，保护 review 内容一致性。
- CLI `--require-pass` 对失败结果返回 `1`，保护自动化 gate 行为。

## 运行证据

真实命令输出确认：

- `status=pass`
- `contract_check_ready=True`
- `original_receipt_status` 和 `rebuilt_receipt_status` 一致
- `original_granted_use` 和 `rebuilt_granted_use` 均为 `downstream_governance_lookup_only`
- `original_lookup_key_count=1`
- `rebuilt_lookup_key_count=1`
- `original_promotion_ready=False`
- `rebuilt_promotion_ready=False`
- `passed_check_count=46`
- `failed_check_count=0`

Playwright MCP snapshot 确认页面显示 `Status pass`、`Contract True`、`Failed 0`，并能看到 v1086 source review 和 v1088 index next step。

## 验证

- focused v1088 tests：`6 passed in 0.27s`
- full pytest：`2834 passed in 634.03s`
- source hygiene：`2215/2215 clean`
- py_compile：新增模块、artifact writer、CLI、测试均通过。
- real CLI evidence：输出 JSON/CSV/TXT/MD/HTML sidecar。
- Playwright MCP screenshot：`e/1088/图片/v1088-receipt-check.png`
- `git diff --check` 会在提交前完成。

## 一句话总结

v1088 把 v1087 receipt 从“已记录”推进到“可重建、可比对、可作为下一步 index 输入”的 contract-checked 证据。

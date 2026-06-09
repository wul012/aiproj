# v1048 publication receipt contract check 代码讲解

## 本版目标和边界

v1048 的目标是对 v1047 downstream lookup-only receipt 做 contract check。

它解决的问题是：v1047 已经记录 receipt，但如果 receipt artifact 被篡改，后续 index 可能消费到错误的 consumer、granted use、source digest、lookup key 或 promotion 状态。v1048 从 receipt 内记录的 v1046 source review 重新构造 receipt，并逐项比较 stable fields。

本版不做：

- 不训练模型。
- 不新增 benchmark。
- 不修改 v1047 receipt。
- 不批准 production promotion。
- 不把 contract check pass 解释为模型质量提升。

## 前置链路

v1048 直接承接：

- v1046：review v1045 receipt index。
- v1047：把 v1046 review 记录成 downstream lookup-only receipt。
- v1048：从 v1046 review 重建 v1047 receipt，确认 original/rebuilt 一致。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1048.py`
  - v1048 contract check builder。
  - 定义 summary/receipt stable fields，并执行 original/rebuilt 对比。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1048_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 contract summary 和全部 check rows。

- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1048.py`
  - CLI 入口。
  - 支持输入 v1047 receipt JSON 或目录，支持 `--require-pass` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1048.py`
  - 覆盖可重建 receipt、granted use 篡改、source review 缺失、source digest 篡改、CLI failure 和 output wiring。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1048 next-step 常量，路由到下一步 receipt index。

## 核心数据结构

v1048 输出中最重要的是四组字段：

- `original_summary`：来自 v1047 receipt artifact 的 summary。
- `rebuilt_summary`：从 v1046 source review 重新生成的 receipt summary。
- `original_receipt`：来自 v1047 artifact 的 receipt body。
- `rebuilt_receipt`：重新生成的 receipt body。

`SUMMARY_FIELDS` 保护：

- ready key
- receipt id/type/status
- consumer name
- granted use
- receipt index row count
- source evidence count
- lookup key count
- promotion and approved-for-promotion
- consumer boundary
- model quality claim
- next step
- passed/failed check count

`RECEIPT_FIELDS` 保护：

- receipt ready/id/type/status
- consumer/requested/granted use
- source review path and sha256
- row/evidence counts
- lookup keys
- review id/status
- promotion boundary
- source receipt/index/check/review paths
- next step

## 检查项说明

`_checks` 先做 6 个整体检查：

- source v1046 review 必须存在。
- original/rebuilt status 必须一致。
- original/rebuilt decision 必须一致。
- failed count 必须一致。
- source review digest 必须一致。
- consumer receipts 必须一致。

随后 `_field_checks` 对 summary 和 receipt stable fields 逐项比较。真实运行中共有 46 个检查全部通过。

## 输入输出流程

CLI 流程：

1. `locate_receipt_v1048` 接受 v1047 JSON 或输出目录。
2. `read_json_report` 读取 v1047 receipt。
3. `_resolve_source_review_path` 找到 receipt 内记录的 v1046 source review。
4. `_rebuild_receipt` 从 v1046 review 重建 v1047 receipt。
5. `_checks` 比较 original/rebuilt。
6. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
7. `--require-pass` 下，失败返回非 0。

## 测试覆盖

聚焦测试验证：

- ready receipt 可以通过 contract check。
- summary/body 的 `granted_use` 被篡改为 production promotion 会失败。
- source review path 缺失会失败。
- source review sha256 被篡改会失败。
- CLI 在坏 receipt + `--require-pass` 下返回 1，同时仍写出失败 artifact。
- 输出 writer 和 CLI wiring 都可用。

## 运行证据

运行证据归档在：

- `e/1048/解释/receipt-check-v1048`
- `e/1048/图片/v1048-receipt-check.png`
- `e/1048/解释/说明.md`

真实 CLI 输出确认：

- `status=pass`
- `contract_check_ready=True`
- original/rebuilt receipt status 一致。
- original/rebuilt granted use 一致。
- original/rebuilt promotion ready 都是 false。
- `passed_check_count=46`
- `failed_check_count=0`

Playwright MCP 快照确认 HTML 页面中 `Status=pass`、`Contract=True`、original/rebuilt use、`Failed=0` 和 v1046 source review path 均可见。

## 一句话总结

v1048 把 v1047 receipt 从“已记录”推进到“可由 source review 重建并逐字段验证”的 contract-checked evidence。

# v1078 publication receipt index review 代码讲解

## 本版目标和边界

v1078 的目标是 review v1077 receipt index，确认它仍然是 digest-backed 的 lookup-only 证据，并且下一步仍然只指向 lookup-only receipt recording。它不是新训练版本，也不是生产放行版本；本版只是在治理链路里加一层只读复核。

本版不改变模型质量声明，不开启 promotion，不新增 checkpoint。它解决的是“v1077 这份 receipt index 是否还能稳定作为下游证据入口”。

## 前置链路

- v1075 记录 lookup-only receipt。
- v1076 contract-check v1075 receipt。
- v1077 把 v1075 receipt 与 v1076 check 组合成 receipt index。
- v1078 复核 v1077 receipt index，确认它仍然只适合作为 lookup-only 入口。

这条链路里，v1077 是“index”，v1078 是“review”。

## 关键文件

### `src/minigpt/...review_v1078.py`

`build_...review_v1078()` 读取 v1077 index report，然后做字段级校验。核心检查包括：

- `status` 是否为 `pass`。
- `decision` 是否为 ready。
- `receipt_index_row_count` 是否为 1。
- `lookup_key_count` 是否为 1。
- `source_evidence_count` 是否为 2。
- `lookup_ready` 和 `contract_check_ready` 是否为真。
- `promotion_ready` 是否仍然为 false。
- source receipt / source receipt check / source review / source receipt index 路径是否仍然存在。
- consumer boundary 是否仍然是 `governance_lookup_only`。
- model quality claim 是否仍然是 bounded claim。
- `source_next_step_matches` 是否仍然把链路指回 v1077 review 的上游准备步骤。

### `_review()`

`_review()` 是本版的主体输出，它把已通过检查的 index 包装成 review 语义：

- `review_ready`
- `review_id`
- `review_status`
- `receipt_index_row_count`
- `lookup_keys`
- `source_evidence_count`
- `lookup_ready`
- `contract_check_ready`
- `granted_use`
- `promotion_ready`
- `approved_for_promotion`
- `consumer_boundary`
- `model_quality_claim`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_path`
- `next_step`

### `src/minigpt/...review_v1078_artifacts.py`

artifact writer 输出 JSON、CSV、TXT、Markdown 和 HTML。HTML 页面会直接显示：

- `Status`
- `Review ready`
- `Rows`
- `Lookup keys`
- `Evidence`
- `Failed`

这让人工复核能一眼看到这版只是 lookup-only review，而不是 promotion gate。

### `scripts/review_...v1078.py`

CLI 接收 v1077 index 或输出目录，生成 v1078 review sidecar。它的输出目录是：

`e/1078/解释/receipt-index-review-v1078/`

## 测试覆盖

`tests/test_...review_v1078.py` 覆盖五类场景：

- ready index 可以通过 review。
- granted use 被改坏后失败。
- source digest 缺失后失败。
- source path 漂移后失败。
- artifact writer 与 CLI 能正确导出 JSON/CSV/TXT/Markdown/HTML。

本版还补了 `tests/__init__.py`。这不是功能点，但它是真实工程收口：没有这个文件时，外部同名 `tests` 包会影响本仓库的 helper 导入，造成全量 collection 失败。

## 运行证据

真实 CLI 结果：

- `status=pass`
- `review_ready=True`
- `review_status=approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only`
- `receipt_index_row_count=1`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=22`
- `failed_check_count=0`

Playwright MCP snapshot 确认 HTML 页面显示 `Status pass`、`Review ready True`、`Rows 1`、`Lookup keys 1`、`Evidence 2`、`Failed 0`，并且源路径完整可见。

## 验证

- focused v1078 tests：`5 passed in 0.50s`
- full pytest：`2780 passed in 922.89s`
- source hygiene：`2175/2175 clean`
- py_compile：新增 Python 文件全部通过。

## 一句话总结

v1078 把 v1077 receipt index 再过一层只读 review，并顺手把本地测试包边界收紧，让整套链路更稳。

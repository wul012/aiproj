# v1070 publication receipt index review 代码讲解

## 本版目标和边界

v1070 的目标是审阅 v1069 receipt index，确认它仍然适合作为 lookup-only 的交接输入。

这版不是新治理链，而是继续把 lookup-only receipt 链路收口：v1069 已把 v1067 receipt 与 v1068 contract check 编成索引，v1070 再确认这份索引的路径、摘要、lookup scope 和 next step 没有漂移。

本版不训练模型，不修改 checkpoint，也不允许 production promotion。

## 前置链路

1. v1069：把 v1067 receipt + v1068 contract check 编成 lookup index。
2. v1070：对 v1069 index 做只读 review。
3. v1071：下一步会把 v1070 review 记录成 receipt。

这条链路的价值是让“索引可以继续流转，但必须先经过 review”。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1070.py`
  - 核心 review builder。
  - 读取 v1069 index，逐项验证 lookup-only use、source evidence、路径、next step 和 no-promotion 边界。
  - 输出 `review`、`summary`、`check_rows` 和 `interpretation`。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1070_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML sidecar。
  - HTML 页面用于人工审阅和截图证据。

- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1070.py`
  - CLI 入口。
  - 接收 v1069 index 目录或 JSON。
  - `--require-review-ready` 和 `--require-lookup-ready` 可作为 gate。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1070.py`
  - 覆盖 ready path、granted use 篡改、source evidence 缺失/漂移、artifact/CLI wiring。

- `e/1070/解释/receipt-index-review-v1070/`
  - 真实 CLI 输出，是本版最终证据。

- `e/1070/图片/v1070-receipt-index-review.png`
  - Playwright MCP 截图证据。

## 核心数据结构

### `check_rows`

`check_rows` 的核心检查包括：

- v1069 index 文件是否存在。
- status / decision / failed_count 是否可复核。
- summary 与 body 是否都 ready。
- lookup scope、granted use、consumer boundary、model quality claim 是否仍然是 lookup only。
- source evidence 是否为 2 条并且 digest 存在。
- receipt、receipt check、review、source index 路径是否存在。
- promotion 是否仍然 false。
- next step 是否从 v1069 index 指向 v1070 review。

### `review`

`review` 是下一步 receipt recording 的输入摘要：

- `review_ready`
- `review_status`
- `receipt_index_path`
- `lookup_keys`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_path`
- `next_step`

### `summary`

`summary` 是自动化 gate 的压缩视图，重点字段包括：

- `review_status`
- `receipt_index_row_count`
- `lookup_key_count`
- `source_evidence_count`
- `lookup_ready`
- `contract_check_ready`
- `promotion_ready`
- `passed_check_count`
- `failed_check_count`

## 运行流程

1. CLI 接收 `e/1069/解释/receipt-index-v1069`。
2. `locate_receipt_index_v1070()` 找到 v1069 JSON。
3. `build_..._review_v1070()` 生成 check rows、review、summary 和 interpretation。
4. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
5. `resolve_exit_code()` 根据 `--require-review-ready` / `--require-lookup-ready` 返回退出码。

## 测试覆盖

focused 测试结果：

```text
5 passed in 0.48s
```

测试保护点：

- ready index 能通过 review。
- `granted_use` 改成 production promotion 会失败。
- source evidence digest 丢失会失败。
- source path 漂移会失败。
- sidecar 输出和 CLI wiring 可用。

全量验证待回填：

- full pytest: `2738 passed in 502.11s`
- source hygiene: `status=pass`, `source_count=2142`, `clean_count=2142`, `bom_count=0`, `syntax_error_count=0`, `compatibility_error_count=0`

## 运行证据

真实 CLI 输出确认：

- `status=pass`
- `review_ready=True`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `failed_check_count=0`

Playwright MCP 截图：

- `e/1070/图片/v1070-receipt-index-review.png`

## 一句话总结

v1070 给 v1069 index 加上只读审阅门槛，保证下一步 receipt recording 继续拿到的是可复核、lookup-only 的交接输入。

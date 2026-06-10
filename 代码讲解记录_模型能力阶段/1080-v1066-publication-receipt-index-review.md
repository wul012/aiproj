# v1066 publication receipt index review 代码讲解

## 本版目标和边界

v1066 的目标是审阅 v1065 生成的 `receipt index`，确认它可以作为下一步 receipt recording 的输入。

它解决的不是模型训练能力问题，而是交接证据问题：v1065 已经把 v1063 receipt 和 v1064 contract check 组成 digest-backed lookup index；v1066 再检查这个 index 的 source paths、source evidence digest、lookup-only use、contract-check-ready 和 no-promotion 边界，避免后续模块消费一个漂移或被误读的 index。

本版明确不做三件事：

- 不训练模型，也不修改 checkpoint。
- 不把 `direct_pair_probe_hit` 扩大成生产级模型能力声明。
- 不批准 production promotion。

## 前置链路

本版来自上一轮 publication receipt 链路：

1. v1063：记录 v1062 review 的 downstream lookup-only receipt。
2. v1064：用 v1062 review 重新校验 v1063 receipt。
3. v1065：把 v1063 receipt 和 v1064 check 索引为 digest-backed lookup evidence。
4. v1066：审阅 v1065 index，确认后续只能进入 receipt recording。

这条链路的关键价值是保持“模型能力保守、治理证据可查、交接输入可复核”。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1066.py`
  - 核心 review builder。
  - 读取 v1065 index JSON，校验 source evidence、lookup scope、granted use、source paths 和 next-step。
  - 输出结构化 `summary`、`review`、`check_rows` 和 `interpretation`。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1066_artifacts.py`
  - 负责 JSON/CSV/TXT/Markdown/HTML sidecar 渲染。
  - HTML 页面用于人工审阅和 Playwright 截图证据。

- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1066.py`
  - CLI 入口。
  - 支持输入 v1065 index JSON 或输出目录。
  - `--require-review-ready` 和 `--require-lookup-ready` 可把 review 结果变成自动化 gate。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1066.py`
  - 覆盖 ready path、granted use 篡改、source evidence digest 丢失、source path 漂移、artifact/CLI wiring。

- `e/1066/解释/receipt-index-review-v1066/`
  - 保存真实 CLI 运行产物。
  - 这些产物是 v1066 的最终证据，不是临时测试文件。

- `e/1066/图片/v1066-receipt-index-review.png`
  - Playwright MCP 截取的 HTML 页面截图，用于证明人可读报告能打开且关键字段可见。

## 核心数据结构

### `check_rows`

`check_rows` 是本版最重要的判断明细。每个 row 形如：

```json
{
  "id": "lookup_ready",
  "status": "pass",
  "actual": {"summary": true, "index": true},
  "detail": "receipt index must be lookup-ready"
}
```

它保护以下问题：

- v1065 index 文件是否存在。
- index status 和 decision 是否为 ready。
- summary 与 index body 是否同时 ready。
- lookup scope 和 granted use 是否仍是 downstream lookup only。
- source evidence 是否有 2 条，并且 digest 存在。
- receipt、receipt check、source review、source index 路径是否仍可访问。
- production promotion 是否仍然为 false。
- v1065 的 next step 是否确实指向 review。

### `review`

`review` 是给后续 receipt recording 消费的只读摘要：

- `review_ready`
- `review_id`
- `review_status`
- `receipt_index_path`
- `lookup_keys`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_path`
- `next_step`

这里的 `next_step` 指向 v1066 receipt recording，表示 v1066 只批准“继续记录治理 receipt”，不批准模型上线。

### `summary`

`summary` 是自动化 gate 的压缩视图。重点字段包括：

- `randomized_holdout_publication_..._review_v1066_ready`
- `lookup_ready`
- `contract_check_ready`
- `promotion_ready`
- `approved_for_promotion`
- `passed_check_count`
- `failed_check_count`

CI 或后续脚本可以只看 summary 判断是否继续。

## 运行流程

1. CLI 接收 `e/1065/解释/receipt-index-v1065`。
2. `locate_receipt_index_v1066()` 在目录中找到 v1065 JSON。
3. `read_json_report()` 读取 JSON object。
4. `build_..._review_v1066()` 生成 check rows、review、summary 和 interpretation。
5. artifact writer 同步输出 JSON/CSV/TXT/Markdown/HTML。
6. CLI 根据 `--require-review-ready`、`--require-lookup-ready` 返回退出码。

## 测试覆盖

本版 focused 测试结果：

```text
5 passed in 0.49s
```

测试保护点：

- ready index 可以通过 review，且 next step 指向 v1066 receipt recording。
- `granted_use` 被改成 production promotion 时失败。
- source evidence digest 缺失时失败。
- source receipt path 漂移时失败。
- JSON/CSV/TXT/Markdown/HTML 输出和 CLI wiring 都可用。

全量验证结果待回填：

- full pytest: `2717 passed in 788.02s`
- source hygiene: `2126/2126 clean`

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

- `e/1066/图片/v1066-receipt-index-review.png`

截图证明 HTML report 能真实打开，并且页面中展示了 Status、Review ready、Rows、Lookup keys、Evidence 和 Failed 这些关键字段。

## 一句话总结

v1066 把 v1065 index 从“可查证据包”推进成“已审阅的 lookup-only 交接输入”，让下一步 receipt recording 有清楚边界和可复核依据。

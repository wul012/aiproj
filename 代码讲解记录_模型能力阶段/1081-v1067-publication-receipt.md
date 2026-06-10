# v1067 publication receipt 代码讲解

## 本版目标和边界

v1067 的目标是把 v1066 receipt index review 记录成 downstream governance lookup-only receipt。

前一版 v1066 已经确认 v1065 index 可以作为 lookup-only handoff evidence；但 review 只是判断结果，后续链路还需要一份 receipt 来表达“这份 review 被哪个消费者读取、授权用途是什么、是否仍然禁止 promotion”。v1067 就是这个 receipt recording 层。

本版不做模型训练，不扩大模型质量声明，不批准 production promotion。

## 前置链路

1. v1065：索引 v1063 receipt 和 v1064 contract check。
2. v1066：审阅 v1065 index，确认它只适合 lookup-only receipt recording。
3. v1067：记录 v1066 review 的 downstream lookup-only receipt。

这保持了项目当前的边界：治理证据可以继续流转，但模型能力仍然只停留在 bounded claim。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067.py`
  - 核心 receipt builder。
  - 校验 v1066 review 的 ready status、lookup-only granted use、source evidence、source paths 和 no-promotion 边界。
  - 生成 `receipt`、`consumer_receipts`、`summary`、`check_rows`。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067_artifacts.py`
  - 负责输出 JSON/CSV/TXT/Markdown/HTML。
  - CSV 聚焦 consumer receipt 行，HTML 聚焦 receipt boundary 和 checks。

- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067.py`
  - CLI 入口。
  - 支持输入 v1066 review JSON 或目录。
  - `--require-receipt-ready` 可作为自动化 gate。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1067.py`
  - 覆盖 ready path、requested use 改成 production、source review path 漂移、source evidence status 变化、失败退出码、artifact/CLI wiring。

- `e/1067/解释/receipt-v1067/`
  - 保存真实 CLI 产物，是本版最终证据。

- `e/1067/图片/v1067-receipt.png`
  - Playwright MCP 截图证据。

## 核心数据结构

### `receipt`

`receipt` 是本版主产物，关键字段包括：

- `receipt_ready`
- `receipt_id`
- `receipt_status`
- `consumer_name`
- `requested_use`
- `granted_use`
- `receipt_index_review_path`
- `receipt_index_review_sha256`
- `source_receipt_index_path`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_origin_path`
- `next_step`

其中 `granted_use` 必须是 `downstream_governance_lookup_only`，`promotion_ready` 和 `approved_for_promotion` 必须保持 false。

### `consumer_receipts`

`consumer_receipts` 把 receipt 映射到具体 lookup key：

```json
{
  "consumer_name": "...v1067_lookup_reader",
  "lookup_key": "publication-receipt-index-...",
  "source_receipt_id": "...v1063",
  "receipt_id": "...v1067",
  "granted_use": "downstream_governance_lookup_only",
  "promotion_ready": false
}
```

这让后续 contract check 可以确认消费凭据没有被篡改。

### `check_rows`

`check_rows` 覆盖：

- v1066 review 文件是否存在。
- review 是否 pass。
- review decision 是否 ready。
- requested use 是否仍是 downstream lookup only。
- source evidence 是否为 2 条且状态 pass。
- source review、source receipt index、source receipt、source check 路径是否仍存在。
- promotion 是否仍为 false。
- next step 是否从 v1066 review 指向 receipt recording。

## 运行流程

1. CLI 接收 `e/1066/解释/receipt-index-review-v1066`。
2. `locate_receipt_index_review_v1067()` 找到 v1066 review JSON。
3. `build_..._receipt_v1067()` 生成 checks、receipt、consumer receipts 和 summary。
4. artifact writer 写出 JSON/CSV/TXT/Markdown/HTML。
5. `--require-receipt-ready` 决定失败时是否返回非零退出码。

## 测试覆盖

focused 测试结果：

```text
6 passed in 0.53s
```

测试保护点：

- ready review 能生成 receipt。
- requested use 改成 production promotion 时失败。
- source review path 漂移时失败。
- source evidence status 变成 fail 时失败。
- 不 ready 时 CLI 在 `--require-receipt-ready` 下返回 1。
- JSON/CSV/TXT/Markdown/HTML 输出和 CLI wiring 可用。

全量验证待回填：

- full pytest: `2723 passed in 656.04s`
- source hygiene: `2130/2130 clean`

## 运行证据

真实 CLI 输出确认：

- `status=pass`
- `receipt_ready=True`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `failed_check_count=0`

Playwright MCP 截图：

- `e/1067/图片/v1067-receipt.png`

## 一句话总结

v1067 把 v1066 的 review 判断落成可消费的 lookup-only receipt，让治理链路继续可复核，同时不越过模型能力边界。

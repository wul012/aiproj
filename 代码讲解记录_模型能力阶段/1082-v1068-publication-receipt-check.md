# v1068 publication receipt contract check 代码讲解

## 本版目标和边界

v1068 的目标是对 v1067 receipt 做 contract check，确认它能从 v1066 receipt index review 重新推导。

这版不是新的治理链，而是给 v1067 receipt 增加防篡改、防路径漂移、防字段误用的复核入口。它仍然不训练模型，不修改 checkpoint，也不把 lookup-only receipt 解读成 production promotion。

## 前置链路

1. v1066：审阅 v1065 receipt index。
2. v1067：记录 v1066 review 的 lookup-only receipt。
3. v1068：从 v1066 review 重新构造 expected receipt，并与 v1067 actual receipt 逐字段对比。

这条链路的核心是“证据可以消费，但消费结果必须能回放”。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1068.py`
  - contract check builder。
  - 从 receipt 中定位 `receipt_index_review_path`。
  - 重新调用 v1067 receipt builder，生成 rebuilt receipt。
  - 对 status、decision、failed_count、digest、consumer receipts、summary fields、receipt fields 做逐项比较。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1068_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - CSV 记录所有 check rows，HTML 负责人可读审阅。

- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1068.py`
  - CLI 入口。
  - `--require-pass` 可以把 contract check 失败转成非零退出码。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1068.py`
  - 覆盖正常重建、granted use 篡改、source review 缺失、source digest 篡改、CLI failure exit、artifact/CLI wiring。

- `e/1068/解释/receipt-check-v1068/`
  - 真实 contract check 输出。

- `e/1068/图片/v1068-receipt-check.png`
  - Playwright MCP 截图证据。

## 核心数据结构

### `SUMMARY_FIELDS`

`SUMMARY_FIELDS` 固定比较 receipt summary 的关键字段：

- ready key
- `receipt_id`
- `receipt_status`
- `consumer_name`
- `granted_use`
- `receipt_index_row_count`
- `source_evidence_count`
- `lookup_key_count`
- `promotion_ready`
- `approved_for_promotion`
- `consumer_boundary`
- `model_quality_claim`
- `next_step`
- check count

这保证 v1067 receipt 的摘要不会被手动改成 promotion-ready 或换成其他 use。

### `RECEIPT_FIELDS`

`RECEIPT_FIELDS` 比较 receipt body：

- `requested_use`
- `granted_use`
- `receipt_index_review_path`
- `receipt_index_review_sha256`
- `lookup_keys`
- `source_receipt_index_path`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_origin_path`

这里保护的是路径链和 digest 链。

### `check_rows`

`check_rows` 包含三类检查：

- source review 文件存在。
- top-level status/decision/failed_count/digest/consumer receipts 一致。
- summary 与 receipt 字段逐项一致。

真实运行中共有 46 个检查通过，失败数为 0。

## 运行流程

1. CLI 接收 `e/1067/解释/receipt-v1067`。
2. `locate_receipt_v1068()` 定位 receipt JSON。
3. builder 从 receipt 里解析 `receipt_index_review_path`。
4. `_rebuild_receipt()` 读取 v1066 review 并重新调用 v1067 receipt builder。
5. `_checks()` 比较 original 和 rebuilt。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。

## 测试覆盖

focused 测试结果：

```text
6 passed in 0.28s
```

测试保护点：

- 可重建 receipt 通过。
- `granted_use` 被改成 production promotion 时失败。
- source review 丢失时失败。
- source review digest 被改坏时失败。
- `--require-pass` 在失败时返回 1。
- sidecar 输出和 CLI wiring 可用。

全量验证待回填：

- full pytest: `2729 passed in 684.80s`
- source hygiene: `2134/2134 clean`

## 运行证据

真实 CLI 输出确认：

- `status=pass`
- `contract_check_ready=True`
- `original_granted_use=downstream_governance_lookup_only`
- `rebuilt_granted_use=downstream_governance_lookup_only`
- `original_promotion_ready=False`
- `rebuilt_promotion_ready=False`
- `passed_check_count=46`
- `failed_check_count=0`

Playwright MCP 截图：

- `e/1068/图片/v1068-receipt-check.png`

## 一句话总结

v1068 让 v1067 receipt 具备可重建、可比对、可失败退出的 contract check，为下一步 digest-backed index 提供可信输入。

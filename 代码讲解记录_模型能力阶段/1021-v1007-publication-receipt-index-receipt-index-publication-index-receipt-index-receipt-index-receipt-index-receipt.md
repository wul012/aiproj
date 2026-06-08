# v1007 publication receipt index receipt index publication index receipt index receipt index receipt index receipt

本版目标是把 v1006 审阅通过的 lookup-only receipt index 记录成 downstream consumer receipt。它解决的问题是：v1006 已经确认 v1005 index 可以进入下一层 receipt recording，但后续 contract check 需要一份稳定、可重建、带 consumer receipt row 的 receipt artifact。

本版不训练模型，不生成 checkpoint，不扩大模型质量声明，不允许 production promotion。它只记录 lookup-only receipt，并把所有 blocked uses 原样保留。

## 前置路线

v1005 把 v1003 receipt 和 v1004 contract check 聚合成 receipt index。v1006 对这份 index 做 review，确认 lookup scope、granted use、source evidence、source path 和 no-promotion 边界都满足要求。

v1007 接收 v1006 review，不重新审阅 v1005 index 的全部字段，而是检查 v1006 review 的结果是否仍然可用，然后生成 downstream receipt。这样后续 v1008 可以从 v1006 review 重新构造 v1007 receipt，检查 receipt artifact 是否被篡改。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007.py`
  - v1007 核心 receipt builder。读取 v1006 review report，执行 21 项检查，生成 receipt、consumer_receipts、summary 和 interpretation。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007.py`
  - CLI 入口。支持输入 v1006 review JSON 或输出目录，并支持 `--consumer-name`、`--requested-use`、`--require-receipt-ready`、`--require-promotion-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007.py`
  - 覆盖 ready receipt、requested use 漂移、source receipt index 缺失、CLI require 失败、输出层和 CLI 默认 consumer。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v1007 receipt 的下一跳：`check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007`。
- `src/minigpt/__init__.py`
  - 暴露 v1007 build/write lazy export。
- `e/1007/解释/receipt-v1007/*`
  - 本版真实运行证据。
- `e/1007/图片/v1007-receipt.png`
  - Playwright MCP 截图证据。

## 输入输出

输入是 v1006 review JSON：

```text
e/1006/解释/review-v1006/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006.json
```

核心输出包括：

- `receipt_index_review_path`
  - v1006 review 文件路径。
- `receipt_index_review_sha256`
  - v1006 review 的 SHA-256，用于后续重建比对。
- `source_receipt_index_review_summary`
  - v1006 summary 快照。
- `source_receipt_index_review`
  - v1006 review body。
- `receipt_index_rows`
  - v1006 传下来的 v1005 index row。
- `source_evidence_rows`
  - v1006 传下来的 digest-backed evidence rows。
- `consumer_receipts`
  - 本版生成的 downstream consumer receipt row。
- `receipt`
  - receipt body。
- `summary`
  - README、CLI、HTML 和后续 check 的稳定摘要。

## 核心检查

`_checks()` 保护以下内容：

- v1006 review 文件存在。
- v1006 review report 本身是 `pass`。
- v1006 decision 和 ready flag 正确。
- v1006 `review_status` 必须是 `approved_for_publication_index_receipt_index_receipt_index_receipt_index_receipt_lookup_only`。
- requested use 必须保持 `downstream_governance_lookup_only`。
- blocked uses 必须完整。
- receipt index 与 lookup 都必须 ready。
- source contract check 必须 ready。
- index row 数量必须等于 1。
- source evidence 数量必须等于 2。
- lookup key 必须使用 `publication-index-receipt-index-receipt-index-receipt:` 命名空间。
- index row 不得 promotion。
- summary、review 和 approved flag 都不得打开 promotion。
- consumer boundary 必须保持 governance lookup only。
- model quality claim 必须保持 bounded。
- source receipt index、source receipt 和 source check 文件必须仍然存在。
- v1006 failed check count 必须是 0。
- v1006 next step 必须指向 record receipt。

这些检查让 receipt recording 不只是复制 v1006 的结论，而是确认 review 仍然处在正确边界里。

## Receipt 语义

通过时，`_receipt()` 输出：

```text
receipt_ready=True
receipt_id=randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-index-receipt-index-receipt-v1007
receipt_type=randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index
receipt_status=publication_index_receipt_index_receipt_index_receipt_index_lookup_receipted
consumer_name=publication_index_receipt_index_receipt_index_receipt_index_governance_lookup_reader
granted_use=downstream_governance_lookup_only
promotion_ready=False
approved_for_promotion=False
```

下一跳：

```text
check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007
```

## Artifact 输出

输出层生成：

- JSON：后续 v1008 contract check 的机器输入。
- CSV：consumer receipt row。
- TXT：终端摘要。
- Markdown：人工审阅归档。
- HTML：浏览器复核和截图。

HTML 展示 receipt boundary、consumer receipts 和 check rows。截图中可以直接看到 receipt status、consumer、source review、source receipt index、source receipt、source check 和 next step。

## 测试覆盖

测试覆盖：

- ready v1006 review 可以生成 pass receipt。
- summary 中的 receipt status、consumer name、granted use、lookup key count、source evidence count、promotion flag 和 next step 符合预期。
- requested use 改成 `production_promotion` 会触发 `requested_use_allowed` 失败。
- source receipt index path 缺失会触发 `source_receipt_index_file_exists` 失败。
- CLI 在 `--require-receipt-ready` 下遇到坏 review 会返回 1。
- CLI 默认 consumer name 必须与 core builder 默认值一致。
- 输出层覆盖 JSON/CSV/TXT/Markdown/HTML。

focused 测试：

```text
5 passed in 6.07s
```

source encoding：

```text
status=pass
source_count=1890
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

full pytest：

```text
2408 passed in 427.71s (0:07:07)
```

## 运行证据

真实运行命令：

```text
python scripts\record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1007.py e\1006\解释\review-v1006 --out-dir e\1007\解释\receipt-v1007 --require-receipt-ready --force
```

输出确认：

```text
status=pass
receipt_ready=True
receipt_status=publication_index_receipt_index_receipt_index_receipt_index_lookup_receipted
consumer_name=publication_index_receipt_index_receipt_index_receipt_index_governance_lookup_reader
granted_use=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=21
failed_check_count=0
```

Playwright MCP 截图：

```text
e/1007/图片/v1007-receipt.png
```

## 一句话总结

v1007 把 v1006 审阅通过的 index 结论记录成 downstream lookup-only receipt，并为下一步 contract check 建立了可重建的 receipt 输入。

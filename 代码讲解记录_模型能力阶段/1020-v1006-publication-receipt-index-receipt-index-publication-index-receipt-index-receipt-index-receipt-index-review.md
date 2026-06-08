# v1006 publication receipt index receipt index publication index receipt index receipt index receipt index review

本版目标是审阅 v1005 生成的 lookup-only receipt index，确认它可以作为下一步 receipt recording 的输入。它解决的问题是：v1005 已经把 v1003 receipt 和 v1004 contract check 聚合为一份索引，但后续如果直接消费这份索引，需要先确认索引的 lookup scope、granted use、digest evidence、source path 和 no-promotion 边界没有漂移。

本版不训练模型，不生成 checkpoint，不提升模型质量声明，不打开 production promotion，也不新增训练数据。它只做一层 contract-preserving review。

## 前置路线

v1003 记录了 v1002-reviewed receipt-index-receipt index 的 lookup-only downstream receipt。v1004 从 v1002 review 重建 v1003 receipt，证明 receipt 字段没有漂移。v1005 再把 v1003 receipt 与 v1004 check 放进一份 receipt index。

v1006 就接在 v1005 之后：它不重新生成 index，而是读取 v1005 index，检查 index body、summary、row、source evidence 和 source path 是否一致。通过后，下一步才可以记录新的 downstream receipt。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006.py`
  - v1006 核心 review builder。读取 v1005 index report，执行 25 项检查，输出 review、summary、issues 和 interpretation。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。HTML 用于浏览器审阅和截图。
- `scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1006.py`
  - CLI 入口。支持输入 JSON 文件或 v1005 输出目录，并提供 `--require-review-ready`、`--require-receipt-index-ready`、`--require-promotion-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006.py`
  - 覆盖 ready review、digest 篡改、lookup scope 篡改、body/row path 漂移、CLI 失败退出和 artifacts 渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v1006 review 的下一跳：`record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1006`。
- `src/minigpt/__init__.py`
  - 暴露 v1006 build/write lazy export。
- `e/1006/解释/review-v1006/*`
  - 本版真实运行证据。
- `e/1006/图片/v1006-review.png`
  - Playwright MCP 截图证据。

## 输入输出

输入是 v1005 的 JSON index report：

```text
e/1005/解释/receipt-index-v1005/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005.json
```

核心 builder 输出一个 review report，主要字段包括：

- `status`
  - 全部检查通过时为 `pass`。
- `decision`
  - 通过时为 `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_review_v1006_ready`。
- `receipt_index_path`
  - 被审阅的 v1005 index 文件路径。
- `source_receipt_index_summary`
  - v1005 的 summary 快照。
- `source_receipt_index`
  - v1005 的 index body。
- `receipt_index_rows`
  - v1005 的 lookup rows。
- `source_evidence_rows`
  - v1005 记录的 digest-backed evidence rows。
- `check_rows`
  - 本版 25 项检查。
- `review`
  - 通过后给后续 receipt recording 使用的审阅结果。
- `summary`
  - README、CLI、HTML 和后续模块消费的稳定摘要。

## 核心检查

`_checks()` 保护以下边界：

- v1005 index 文件存在。
- v1005 source report 本身是 `pass`。
- v1005 decision 和 ready flag 是 ready。
- summary 与 body 都标记 `index_ready=True`。
- `lookup_scope` 和 `granted_use` 均保持 downstream governance lookup only。
- `lookup_ready=True`。
- `contract_check_ready=True`。
- receipt index row 数量与 summary 的 `lookup_key_count` 一致，且等于 1。
- lookup key 必须使用 `publication-index-receipt-index-receipt-index-receipt:` 命名空间。
- index row 的 `promotion_ready` 必须是 false。
- source evidence row 数量为 2。
- source evidence row 全部 `status=pass`。
- source evidence digest 必须是 SHA-256。
- source evidence 文件仍然存在。
- source receipt 和 source receipt check 文件仍然存在。
- index body 中的 receipt/check path 与 row path 一致。
- source review 和 source receipt index 文件仍然存在。
- consumer boundary 仍是 governance lookup only。
- model quality claim 仍是 bounded randomized target hidden holdout claim only。
- `promotion_ready` 与 `approved_for_promotion` 都保持 false。
- source failed check count 为 0。
- v1005 next step 必须指向 v1006 review。

这些检查让 v1006 不是“看见一个 JSON 就批准”，而是把索引的核心约束重新读一遍。

## Review 语义

通过时，`_review()` 输出：

```text
review_ready=True
review_status=approved_for_publication_index_receipt_index_receipt_index_receipt_index_receipt_lookup_only
receipt_index_row_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
approved_for_promotion=False
allowed_use=downstream_governance_lookup_only
```

`next_step` 指向：

```text
record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_v1006
```

这说明本版只批准 lookup-only receipt recording，不批准生产提升。

## Artifact 输出

输出层生成五类文件：

- JSON：后续 receipt recording 的机器输入。
- CSV：展开每个 check row。
- TXT：终端摘要。
- Markdown：归档审阅。
- HTML：浏览器复核与截图。

HTML summary cards 展示 `Status`、`Review ready`、`Receipt index`、`Lookup keys`、`Evidence` 和 `Failed`。Review Boundary 展示 source receipt index、source receipt、source check 和 next step。Checks 表格展开 25 项检查。

这些产物都是最终证据，不是临时文件。

## 测试覆盖

测试覆盖：

- ready v1005 index 可以通过 review。
- summary 中的 `review_status`、`receipt_index_ready`、`lookup_key_count`、`source_evidence_count`、`promotion_ready` 和 `next_step` 符合预期。
- 修改 source evidence digest 会触发 `source_evidence_digests` 失败。
- 把 `lookup_scope` 改成 `production_promotion` 会触发 `lookup_scope_downstream` 失败。
- 修改 row 中的 source receipt path 会触发 `source_paths_match_rows` 失败。
- CLI 在 `--require-review-ready` 下遇到篡改 index 会返回 1。
- artifacts 输出 JSON/CSV/TXT/Markdown/HTML，并且 CLI 可以通过目录输入定位 v1005 JSON。

focused 测试结果：

```text
6 passed in 10.08s
```

source encoding：

```text
status=pass
source_count=1886
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

full pytest：

```text
2403 passed in 481.65s (0:08:01)
```

## 运行证据

真实运行命令：

```text
python scripts\review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1006.py e\1005\解释\receipt-index-v1005 --out-dir e\1006\解释\review-v1006 --require-review-ready --require-receipt-index-ready --force
```

输出确认：

```text
status=pass
review_ready=True
receipt_index_ready=True
lookup_key_count=1
source_evidence_count=2
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

Playwright MCP 截图：

```text
e/1006/图片/v1006-review.png
```

截图快照确认 HTML 展示 `Status=pass`、`Review ready=True`、`Lookup keys=1`、`Evidence=2`、`Failed=0`。

## 一句话总结

v1006 把 v1005 lookup-only receipt index 从“可读取的索引产物”推进到“已审阅、可进入下一层 receipt recording 的治理输入”，同时继续阻断生产提升。

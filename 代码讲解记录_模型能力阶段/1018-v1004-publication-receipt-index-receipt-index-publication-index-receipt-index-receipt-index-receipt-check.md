# v1004 publication receipt index receipt index publication index receipt index receipt index receipt check

本版目标是对 v1003 receipt 做 contract check：从 v1003 记录的源 v1002 review 重新构建 receipt，然后逐字段比较原始 receipt 与重建 receipt。它解决的问题是：v1003 已经把 receipt-index-receipt index 记录为 lookup-only receipt，但还需要证明这份 receipt 不是被手工篡改出来的，也没有丢失 source review、consumer、granted use、no-promotion 等关键边界。

本版不训练模型，不生成 checkpoint，不扩大模型质量声明，不允许 production promotion。它只验证 v1003 receipt 的可重建性，并把下一步路由到 index。

## 前置路线

v1001 生成 receipt-index-receipt index。v1002 review 这份 index，确认它可被下游 receipt 消费。v1003 记录 lookup-only downstream receipt。v1004 则从 v1003 receipt 里记录的 `receipt_index_review_path` 找回 v1002 review，重新调用 v1003 builder，确认重建结果与原始归档一致。

这条路线的价值是让治理证据不是“只相信保存下来的 JSON”，而是可以沿 source review 重新推导。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_check_v1004.py`
  - v1004 核心 checker。读取 v1003 receipt report，定位 source v1002 review，重建 v1003 receipt，并比较稳定字段。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_check_v1004_artifacts.py`
  - v1004 输出层。负责 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1004.py`
  - CLI 入口。支持 JSON 或输出目录，支持 `--require-pass` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_check_v1004.py`
  - 单测覆盖正常重建、granted use 篡改、source review 缺失、source digest 篡改、CLI 失败退出和输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v1004 next step 常量：`index_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1004`。
- `src/minigpt/__init__.py`
  - 暴露 v1004 build/write 懒加载入口。
- `e/1004/解释/receipt-check-v1004/*`
  - v1004 真实运行证据。
- `e/1004/图片/v1004-receipt-check.png`
  - Playwright MCP 截图，证明 HTML 报告能被浏览器审阅。

## 输入输出

v1004 输入是 v1003 receipt JSON 或其输出目录。`locate_receipt_v1004()` 如果收到目录，会自动补上 v1003 JSON 文件名：

```text
randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.json
```

`_resolve_source_review_path()` 从两个位置读取 source review：

- report 顶层的 `receipt_index_review_path`
- receipt body 的 `receipt_index_review_path`

如果路径不是绝对路径，会先尝试相对当前工作目录，再尝试相对 receipt JSON 所在目录。这样既支持项目根目录运行，也支持未来复制到归档目录后做相对路径检查。

v1004 输出包含：

- `original_summary`
- `rebuilt_summary`
- `original_receipt`
- `rebuilt_receipt`
- `check_rows`
- `summary`
- `interpretation`

其中 `summary.contract_check_ready=True` 只表示 receipt 可重建，不表示模型可推广。

## 重建逻辑

`_rebuild_receipt()` 的逻辑很窄：

1. 如果 source review 路径不存在，返回空对象。
2. 读取 v1002 review JSON。
3. 调用 v1003 builder：

```python
build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003(
    read_review_json(source_review),
    receipt_index_review_path=source_review,
)
```

这意味着 v1004 不是重新解释 v1003 产物，而是复用 v1003 的生产逻辑重新生成一份 receipt。只要原始 JSON 被篡改，稳定字段比较就会失败。

## 检查字段

顶层检查包括：

- source v1002 review 文件存在。
- `status` 能重建一致。
- `decision` 能重建一致。
- `failed_count` 能重建一致。
- `receipt_index_review_sha256` 能重建一致。
- `consumer_receipts` 能重建一致。

`SUMMARY_FIELDS` 检查：

- v1003 ready flag
- receipt id/type/status
- consumer name
- granted use
- receipt index row count
- source evidence count
- lookup key count
- promotion flags
- consumer boundary
- blocked uses
- next step
- passed/failed check count

`RECEIPT_FIELDS` 检查：

- receipt ready/id/type/status
- consumer name
- requested/granted use
- receipt index review path
- receipt index row count
- source evidence count
- lookup keys
- review id/status
- blocked uses
- promotion flags
- consumer boundary
- model quality claim
- source receipt index/receipt/check paths
- next step

这些字段合在一起，保护的是“v1003 receipt 的来源、用途、读者、边界和后续路由是否还能被源 review 重新推导出来”。

## Artifact 输出

输出层生成五类产物：

- JSON：机器可读的 contract check report。
- CSV：44 条 check row 的表格。
- TXT：CLI 摘要，显示 status、contract readiness、原始/重建状态、use、lookup key count 和 next step。
- Markdown：归档审阅。
- HTML：浏览器审阅和截图。

HTML 页面包含两个重点：

- Contract Summary：展示 source review、原始/重建 receipt status、promotion flag 和 next step。
- Checks：展示 44 条逐字段检查。

这份 HTML 不是单纯展示，它是人工确认 v1004 contract check 没有隐藏失败项的证据。

## 测试覆盖

单测覆盖：

- ready v1003 receipt 可以通过 contract check。
- v1003 receipt 的 `summary.granted_use` 和 `receipt.granted_use` 被篡改为 `production_promotion` 会失败。
- source review 路径丢失会失败。
- `receipt_index_review_sha256` 被篡改会失败。
- CLI `--require-pass` 在失败报告下返回 1。
- 输出层覆盖 JSON/CSV/TXT/Markdown/HTML。

focused 测试结果：

```text
6 passed in 6.80s
```

source encoding 结果：

```text
status=pass
source_count=1878
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

最终收口还包括：

```text
git diff --check: pass, only Git line-ending warnings
full pytest: 2393 passed in 367.10s (0:06:07)
```

## 运行证据

真实运行命令：

```powershell
python scripts\check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1004.py e\1003\解释\receipt-v1003 --out-dir e\1004\解释\receipt-check-v1004 --require-pass --force
```

输出显示：

- `status=pass`
- `contract_check_ready=True`
- `failed_count=0`
- original/rebuilt receipt status 都是 `publication_index_receipt_index_receipt_index_lookup_receipted`
- original/rebuilt granted use 都是 `downstream_governance_lookup_only`
- original/rebuilt promotion 都是 `False`
- `passed_check_count=44`
- `failed_check_count=0`

截图位于 `e/1004/图片/v1004-receipt-check.png`，页面显示 contract true、failed 0、lookup-only use 和下一步 index 路由。

## 一句话总结

v1004 把 v1003 receipt 从“已记录”推进到“可从源 review 重建且稳定字段完全一致”，为后续索引和继续治理提供了更硬的证据入口。

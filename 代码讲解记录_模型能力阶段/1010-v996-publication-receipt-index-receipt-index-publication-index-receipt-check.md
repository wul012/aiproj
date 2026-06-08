# v996 publication receipt index receipt index publication index receipt check

本版目标是 contract-check v995 receipt。它读取 v995 receipt 内记录的 v994 review 路径，重新构建一份 receipt，然后比较 original/rebuilt 的稳定字段。这样可以防止 receipt JSON 被手工篡改、路径丢失，或者 granted use / promotion 字段发生漂移。

本版不训练模型，不改变 checkpoint，不生成新的消费授权，只验证 v995 receipt 是否能从源 review 复现。

## 前置路线

v994 review 确认 v993 publication index 只能用于 lookup-only receipt。v995 基于 v994 review 记录 downstream consumer receipt。v996 反向复核：如果 v995 receipt 真的是从 v994 review 得来，那么重新构建时关键字段必须一致。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996.py`
  - 核心 contract check builder。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_v996.py`
  - CLI 入口，支持 `--require-pass`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996.py`
  - 覆盖 rebuild 通过、granted use 篡改、source review 缺失、CLI 失败码和输出层。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v996 下一步路由。
- `src/minigpt/__init__.py`
  - 暴露 v996 build/write 包级入口。

## 核心流程

`build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_check_v996()` 的流程是：

1. 读取 original v995 receipt 的 `summary` 和 `receipt`。
2. 从 `publication_index_review_path` 找到源 v994 review。
3. 调用 v995 builder 重新构建 receipt。
4. 比较 original/rebuilt 的 `status`、`decision`、`failed_count`、`consumer_receipts`。
5. 比较 `SUMMARY_FIELDS` 和 `RECEIPT_FIELDS` 中列出的稳定字段。
6. 输出 contract check report。

如果 source review 不存在，或者 original 被篡改，check 会失败。

## 字段语义

`SUMMARY_FIELDS` 覆盖 receipt ready、receipt id、receipt type、receipt status、consumer name、granted use、publication index row count、source evidence count、lookup key count、promotion 状态、consumer boundary、blocked uses、next step、passed/failed check count。

`RECEIPT_FIELDS` 覆盖 receipt body 内的 requested/granted use、source review path、lookup keys、review status、blocked uses、promotion 状态、source publication/check path 和下一步路由。

这些字段是后续 index 或 downstream reader 最可能依赖的字段，因此必须能从 v994 review 重建。

## 测试覆盖

测试覆盖：

- ready v995 receipt 能 contract-check 通过。
- 将 `summary.granted_use` 和 `receipt.granted_use` 改为 `production_promotion` 会失败。
- source review path 改为不存在会失败。
- CLI 在 `--require-pass` 下遇到篡改 receipt 会返回 1。
- 输出层能生成 JSON、CSV、TXT、Markdown、HTML。

这让 v996 同时保护内容一致性、源路径、CLI 退出码和报告产物。

## 运行证据

真实运行使用 `e/995/解释/publication-receipt-index-receipt-index-publication-index-receipt-v995` 作为输入，输出写入 `e/996/解释/publication-receipt-index-receipt-index-publication-index-receipt-check-v996/`。

结果为：

- `status=pass`
- `contract_check_ready=True`
- `original_receipt_status=publication_index_lookup_receipted`
- `rebuilt_receipt_status=publication_index_lookup_receipted`
- `original_granted_use=downstream_governance_lookup_only`
- `rebuilt_granted_use=downstream_governance_lookup_only`
- `original_lookup_key_count=1`
- `rebuilt_lookup_key_count=1`
- `original_promotion_ready=False`
- `rebuilt_promotion_ready=False`
- `failed_check_count=0`
- `passed_check_count=42`

Playwright MCP 截图保存在 `e/996/图片/`，证明 HTML 报告可打开，并展示 original/rebuilt 对比表。

## 一句话总结

v996 让 v995 receipt 从“已记录”升级为“可从源 review 复现”，降低下游 lookup 证据漂移风险。

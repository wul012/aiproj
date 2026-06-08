# v999 publication receipt index receipt index publication index receipt index receipt

本版目标是把 v998 review 的通过结论记录成一个 lookup-only receipt。它解决的问题是：v998 已经证明 v997 receipt index 可作为后续 receipt 记录入口，但后续 contract check 和索引层需要一个稳定 receipt artifact，而不是直接消费 review 报告。

本版不训练模型，不修改 checkpoint，不扩张模型质量声明，也不允许 production promotion。它只记录治理消费关系。

## 前置路线

v997 把 v995 receipt 与 v996 contract check 合并为一个 `publication-index-receipt:` receipt index。v998 复核这个 index，确认 source evidence、路径、lookup scope、contract check 和 no-promotion 字段没有漂移。v999 消费 v998 review，记录 downstream consumer receipt。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.py`
  - v999 核心 receipt builder。它读取 v998 review，生成 `receipt`、`consumer_receipts`、`check_rows` 和 summary。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。CSV 以 consumer receipt 为主，HTML 用于截图验证。
- `scripts/record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.py`
  - CLI 入口，支持 `--consumer-name`、`--requested-use`、`--require-receipt-ready` 和 `--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.py`
  - 覆盖 ready receipt、requested use 篡改、source receipt index 缺失、CLI 失败退出和输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v999 下一步常量：`check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999`。
- `src/minigpt/__init__.py`
  - 暴露 v999 build/write 包级懒加载入口。

## 核心数据结构

输入是 v998 review report。v999 读取：

- `summary.randomized_holdout_..._review_v998_ready`
- `summary.review_status`
- `summary.receipt_index_ready`
- `summary.lookup_ready`
- `summary.contract_check_ready`
- `summary.blocked_uses`
- `review.receipt_index_path`
- `review.source_receipt_path`
- `review.source_receipt_check_path`
- `receipt_index_rows`
- `source_evidence_rows`

输出的 `receipt` 对象包含：

- `receipt_ready`
- `receipt_id`
- `receipt_type`
- `receipt_status=publication_index_receipt_index_lookup_receipted`
- `consumer_name`
- `requested_use`
- `granted_use=downstream_governance_lookup_only`
- `receipt_index_review_path`
- `receipt_index_row_count`
- `source_evidence_count`
- `lookup_keys`
- `review_id`
- `review_status`
- `blocked_uses`
- `promotion_ready=False`
- `approved_for_promotion=False`
- `consumer_boundary=governance_lookup_only`
- `model_quality_claim=bounded_randomized_target_hidden_holdout_claim_only`
- `source_receipt_index_path`
- `source_receipt_path`
- `source_receipt_check_path`
- `next_step`

`consumer_receipts` 是后续模块主要消费的表格行，它把 consumer、lookup key、receipt index id、source receipt id、receipt id、granted use 和 no-promotion 状态放在一起。

## 检查逻辑

v999 的 `_checks()` 保护这些边界：

- v998 review 文件存在。
- v998 report status、decision、summary ready flag 和 body `review_ready` 都正确。
- review status 必须是 `approved_for_publication_index_receipt_index_receipt_lookup_only`。
- requested use 只能是 `downstream_governance_lookup_only`。
- blocked uses 必须包含 production promotion、model quality expansion 和 training data claim expansion。
- receipt index ready 与 lookup ready 都必须为真。
- contract check ready 必须为真。
- 只允许一条 receipt index row 和两条 source evidence。
- lookup key 必须使用 `publication-index-receipt:` 命名空间。
- index row 不允许 promotion。
- summary/review/approved 三处 promotion 字段都必须为 false。
- consumer boundary 与 model quality claim 必须保持 bounded。
- source receipt index、source receipt、source receipt check 文件都必须存在。
- source review failed check count 必须为 0。
- v998 next step 必须指向本版 receipt。

这些检查让 receipt 不会把 v998 review 偷换成生产发布证明。

## 运行证据

真实运行命令：

```powershell
python scripts/record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999.py e/998/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-review-v998 --out-dir e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999 --require-receipt-ready --force
```

输出显示 `status=pass`、`receipt_ready=True`、`receipt_status=publication_index_receipt_index_lookup_receipted`、`granted_use=downstream_governance_lookup_only`、`lookup_key_count=1`、`source_evidence_count=2`、`promotion_ready=False`、`failed_check_count=0`、`passed_check_count=21`。

Playwright MCP 打开 HTML 后保存快照和截图到 `e/999`，证明 receipt boundary、consumer receipts 和 checks 表在报告中可见。

## 测试覆盖

测试覆盖：

- ready receipt 保护正常链路。
- requested use 篡改保护 lookup-only 边界。
- source receipt index 缺失保护 v998 review 指向的 v997 index 文件。
- CLI 失败退出保护 `--require-receipt-ready`。
- 输出测试覆盖 JSON/CSV/TXT/Markdown/HTML 和 CLI wiring。

## 一句话总结

v999 把 v998 review 转成稳定的 lookup-only receipt，为下一步 contract check 提供可重建、可对比、不可 promotion 的治理产物。

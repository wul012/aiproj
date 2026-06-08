# v992 publication receipt index receipt index publication check

本版目标是检查 v991 lookup-only publication 是否能从 v990 review 重新推导出来。它解决的是 publication artifact 的可信性问题：即使 v991 JSON 被手工改写，v992 也能通过重建对比发现 `published_use`、路径、lookup key、blocked uses 或 promotion 字段漂移。

本版不做模型训练，不生成新 checkpoint，不扩大 randomized holdout 的模型质量声明。它只是给 v991 交付物加一层 contract check，保证后续 index 阶段消费的是可复核 publication。

## 前置路线

v991 把 v990 review 认可的 receipt index receipt index 发布为 `downstream_governance_lookup_only` publication。v992 接在 v991 的 `next_step=check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991` 后面。

这条链路仍然保留同一个边界：允许 downstream governance lookup，拒绝 production promotion、model quality expansion 和 training data claim expansion。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992.py`
  - 核心 check。读取 v991 publication，解析 source v990 review 路径，重新调用 v991 builder，并比较 original/rebuilt 字段。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992_artifacts.py`
  - 输出层。负责 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v992.py`
  - CLI 入口。支持输入 v991 JSON 或目录，`--require-pass` 下失败返回 1。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_check_v992.py`
  - 单测。覆盖重建通过、published use 篡改、source review 丢失、CLI 失败码和输出写入。
- `e/992/解释/publication-receipt-index-receipt-index-publication-check-v992/*`
  - 本版 contract check 证据。
- `e/992/图片/v992-randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-check.png`
  - Playwright MCP 截图证据。

## 核心数据结构

v992 report 保留四类对比对象：

- `original_summary`：v991 publication 原始 summary。
- `rebuilt_summary`：从 v990 review 重新构建 v991 publication 后得到的 summary。
- `original_publication`：v991 原始 publication body。
- `rebuilt_publication`：重建后的 publication body。

`summary` 则压缩出后续最关心的字段：

- `contract_check_ready`
- `source_receipt_index_review`
- `original_publication_status`
- `rebuilt_publication_status`
- `original_published_use`
- `rebuilt_published_use`
- `original_receipt_index_row_count`
- `rebuilt_receipt_index_row_count`
- `original_source_evidence_count`
- `rebuilt_source_evidence_count`
- `original_lookup_key_count`
- `rebuilt_lookup_key_count`
- `original_promotion_ready`
- `rebuilt_promotion_ready`
- `next_step`

这些字段让后续 index 阶段不用直接理解完整 publication JSON，也能快速判断 check 是否通过。

## 核心检查

v992 先检查 `source_receipt_index_review_exists`，确保 v991 指向的 v990 review 还存在。然后比较：

- 顶层 `status`
- 顶层 `decision`
- 顶层 `failed_count`
- 完整 `check_rows`
- 17 个 summary 字段
- 21 个 publication body 字段

其中 summary/body 字段包括 publication ready、publication status、published use、lookup ready、contract check ready、receipt index id、lookup key count、source evidence count、blocked uses、consumer boundary、model quality claim、promotion=false 和 next step。

如果字段不一致，check 会把具体字段写入 `issues`，并在 `--require-pass` 下返回 1。

## 输入输出流程

CLI 使用 `locate_receipt_index_publication_v992` 兼容 v991 输出目录和 JSON 文件。核心 builder 通过 `_resolve_source_review_path` 找到 `receipt_index_review_path`，再调用 v991 builder 重建 publication。最后 artifacts 模块写出五类报告。

真实运行命令为：

```powershell
python scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v992.py e/991/解释/publication-receipt-index-receipt-index-publication-v991 --out-dir e/992/解释/publication-receipt-index-receipt-index-publication-check-v992 --require-pass --force
```

输出显示 `status=pass`、`contract_check_ready=True`、`failed_check_count=0`、`passed_check_count=43`。

## 测试覆盖

聚焦测试覆盖：

- 可重建 publication 通过。
- `published_use` 被篡改为 `production_promotion` 时，summary 和 publication body 两处都失败。
- source review 路径缺失时失败。
- CLI 在 `--require-pass` 下遇到篡改输入返回 1。
- JSON、CSV、TXT、Markdown 和 HTML 输出均生成。

这组测试保护的是 artifact 可复核性，不是只看当前 JSON 是否“看起来 ready”。

## 运行证据

运行证据写入 `e/992/解释/说明.md` 和 `e/992/解释/publication-receipt-index-receipt-index-publication-check-v992/`。HTML 报告通过 Playwright MCP 截图，页面能看到 contract ready、original/rebuilt use、lookup key 数和 checks 表。

## 一句话总结

v992 让 v991 publication 具备可复核的 contract check，确认它仍然只是 downstream lookup-only publication，不是生产提升入口。

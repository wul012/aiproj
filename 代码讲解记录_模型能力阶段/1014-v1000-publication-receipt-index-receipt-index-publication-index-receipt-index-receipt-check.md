# v1000 publication receipt index receipt index publication index receipt index receipt check

本版目标是给 v999 receipt 增加 contract check：从 v999 receipt 内记录的 `receipt_index_review_path` 重新读取 v998 review，重新构建 v999 receipt，然后比较 original 和 rebuilt 的稳定字段。它解决的问题是：receipt artifact 如果被手工改动，后续索引层不能只看 receipt 文件本身，而要能回到源 review 重新推导。

本版不训练模型，不修改 checkpoint，不扩展模型质量声明，也不做 production promotion。它只是防止 lookup-only receipt 被篡改成其他用途。

## 前置路线

v998 复核 v997 receipt index，并把下一步指向 v999 receipt。v999 根据 v998 review 记录 lookup-only receipt。v1000 站在 v999 之后，重新从 v998 review 构建 v999 receipt 并逐字段对比，确认 receipt 没有漂移。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.py`
  - v1000 核心 contract check。它定位 v999 receipt，解析 source review，调用 v999 builder 重建 receipt，再比较 top-level、summary、receipt 和 consumer receipts。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。CSV 保存逐项字段对比，HTML 用于截图。
- `scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v1000.py`
  - CLI 入口，支持输入 v999 JSON 或输出目录，并支持 `--require-pass`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_check_v1000.py`
  - 覆盖可重建 receipt、granted use 篡改、source review 缺失、source digest 篡改、CLI 失败退出和输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v1000 下一步常量：`index_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v1000`。
- `src/minigpt/__init__.py`
  - 暴露 v1000 build/write 包级懒加载入口。

## 核心数据结构

v1000 读取 v999 receipt report。关键输入字段：

- `receipt_index_review_path`
- `receipt_index_review_sha256`
- `summary`
- `receipt`
- `consumer_receipts`

`_resolve_source_review_path()` 先从 top-level `receipt_index_review_path` 找源 review，再从 `receipt.receipt_index_review_path` 兜底。如果路径是相对路径，会先按当前工作目录判断，再尝试相对 receipt 文件目录解析。

`_rebuild_receipt()` 读取源 v998 review，然后调用：

```python
build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v999(...)
```

重建出来的 report 不比较 `generated_at`，因为它本来就是运行时间；其余稳定字段需要一致。

## 对比范围

top-level 对比：

- `status`
- `decision`
- `failed_count`
- `receipt_index_review_sha256`
- `consumer_receipts`

summary 对比：

- ready flag
- `receipt_id`
- `receipt_type`
- `receipt_status`
- `consumer_name`
- `granted_use`
- `receipt_index_row_count`
- `source_evidence_count`
- `lookup_key_count`
- `promotion_ready`
- `approved_for_promotion`
- `consumer_boundary`
- `blocked_uses`
- `next_step`
- check counts

receipt 对比：

- `receipt_ready`
- receipt identity/status/use
- source review path
- row/evidence counts
- lookup keys
- review id/status
- blocked uses
- no-promotion fields
- source receipt index/receipt/check paths
- next step

这些字段覆盖 receipt 的身份、来源、消费者、允许用途、拒绝用途和后续路由。

## 运行证据

真实运行命令：

```powershell
python scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v1000.py e/999/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999 --out-dir e/1000/解释/receipt-index-receipt-check-v1000 --require-pass --force
```

因为 v1000 文件名较长，运行证据目录采用短名 `receipt-index-receipt-check-v1000`，避免 Windows 路径长度限制；报告 title 和文件名仍保留完整语义。

输出显示 `status=pass`、`contract_check_ready=True`、original/rebuilt receipt status 都是 `publication_index_receipt_index_lookup_receipted`、original/rebuilt granted use 都是 `downstream_governance_lookup_only`、original/rebuilt promotion 都是 `False`、`failed_check_count=0`、`passed_check_count=44`。

## 测试覆盖

测试覆盖：

- 正常 receipt 能从 source review 重建。
- granted use 篡改会触发 summary 和 receipt 两处失败。
- source review 缺失会触发 source path 检查失败。
- top-level `receipt_index_review_sha256` 篡改会触发 digest 对比失败。
- CLI `--require-pass` 在失败报告下返回 1，同时仍写出失败报告。
- 输出测试覆盖 JSON/CSV/TXT/Markdown/HTML。

## 一句话总结

v1000 把 v999 receipt 从“已记录”推进到“可重建验证”，让后续索引层可以信任它仍然只是 lookup-only 治理证据。

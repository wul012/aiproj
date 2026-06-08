# v1012 publication receipt index receipt index publication index receipt index receipt index receipt index receipt index receipt check

## 目标与边界

v1012 的目标是对 v1011 lookup-only receipt 做 contract check：读取 receipt 里记录的 source review，重新构建 receipt，再比较原始 receipt 和重建 receipt 是否一致。这样可以防止 receipt JSON 被篡改、source review 路径漂移、summary 字段和 receipt body 不一致。

本版不训练模型，不改变 benchmark，不扩大模型质量声明，也不把 contract check 通过解释为 production promotion。

## 前置路线

1. v1010 审阅 v1009 receipt index，给出 lookup-only receipt recording 许可。
2. v1011 把 v1010 review 记录成 downstream receipt。
3. v1012 从 v1010 review 重新构造 v1011 receipt，证明 v1011 是可复核产物。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1012.py`
  - 核心 contract check builder，负责定位 receipt、解析 source review、重建 receipt、比较字段和输出 summary。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1012_artifacts.py`
  - 负责 JSON、CSV、TXT、Markdown、HTML 输出。
- `scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1012.py`
  - CLI 入口，支持输入 receipt JSON 或 receipt 输出目录。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1012.py`
  - 覆盖 rebuild pass、granted use 篡改、source review 缺失、source digest 篡改、CLI failure 和输出渲染。
- `e/1012/解释/receipt-check-v1012/`
  - 真实运行证据，后续 v1013 index 会消费这里的 JSON。

## 核心数据结构

v1012 report 主要包含：

- `original_summary`
  - v1011 receipt 的 summary。
- `rebuilt_summary`
  - 从 v1010 review 重新构建 receipt 后得到的 summary。
- `original_receipt`
  - v1011 receipt body。
- `rebuilt_receipt`
  - 重建后的 receipt body。
- `check_rows`
  - 字段级检查行，每行包含 `id`、`status`、`actual`、`detail`。
- `summary.contract_check_ready`
  - 全部检查通过才为 `True`。
- `summary.next_step`
  - 指向下一步 receipt index 构建。

## 核心检查

`_checks()` 包含三类检查：

1. 顶层合同检查：
   - source review 文件存在。
   - `status`、`decision`、`failed_count` 必须一致。
   - `receipt_index_review_sha256` 必须一致。
   - `consumer_receipts` 必须一致。

2. summary 字段检查：
   - ready key、receipt id、receipt type、receipt status、consumer name、granted use、row count、evidence count、lookup key count、promotion flags、consumer boundary、blocked uses、next step、passed/failed check count 都必须一致。

3. receipt body 字段检查：
   - receipt ready、receipt id、requested/granted use、source review path、lookup keys、review id/status、blocked uses、promotion flags、model quality claim、source receipt paths、next step 都必须一致。

只要其中一项漂移，`status` 就会变成 `fail`，`--require-pass` 下 CLI 返回 1。

## 输入输出链路

输入：

```text
e/1011/解释/receipt-v1011/...receipt_v1011.json
```

重建来源：

```text
e/1010/解释/review-v1010/...review_v1010.json
```

输出：

```text
e/1012/解释/receipt-check-v1012/...receipt_check_v1012.json
e/1012/解释/receipt-check-v1012/...receipt_check_v1012.csv
e/1012/解释/receipt-check-v1012/...receipt_check_v1012.txt
e/1012/解释/receipt-check-v1012/...receipt_check_v1012.md
e/1012/解释/receipt-check-v1012/...receipt_check_v1012.html
```

JSON 是后续 index 的机器输入；CSV 是字段级检查清单；HTML 与截图用于人工复核。

## 测试覆盖

focused 测试包含：

- 正常 receipt 可以重建并通过。
- granted use 被改成 production promotion 时失败。
- source review 路径缺失时失败。
- source digest 被篡改时失败。
- `--require-pass` 能对坏 receipt 返回 1。
- artifact writer 与 CLI 输出完整串联。

这些测试保护 receipt 的可重建性和 lookup-only 边界，不证明模型生成能力。

## 一句话总结

v1012 把 v1011 receipt 从“已记录”升级为“可从源 review 重建并逐字段验证”，为后续 index 化提供可信输入。

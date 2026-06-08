# v1010 publication receipt index receipt index publication index receipt index receipt index receipt index receipt index review

## 目标与边界

v1010 的目标是审阅 v1009 生成的 receipt index，确认它只适合进入下一步 lookup-only receipt recording。v1009 已经把 v1007 receipt 与 v1008 contract check 合并成 digest-backed index；v1010 负责检查这份 index 的路径、digest、lookup scope、contract check 和 no-promotion 边界。

本版不训练模型，不生成 checkpoint，不扩大模型质量声明，不改变 promotion 结论，也不新开治理链。

## 前置路线

1. v1007 记录 lookup-only downstream receipt。
2. v1008 证明 v1007 receipt 可以从 v1006 review 重建。
3. v1009 将 v1007 receipt 与 v1008 check 收成 receipt index。
4. v1010 review v1009 index，给下一步 receipt recording 一个只读入口。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1010.py`
  - 核心 review builder，负责检查 index、生成 review body 和 summary。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1010_artifacts.py`
  - 负责 JSON、CSV、TXT、Markdown、HTML 输出。
- `scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_v1010.py`
  - CLI 入口。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1010.py`
  - 覆盖 ready 路径、digest 篡改、lookup scope 篡改、路径漂移、CLI 失败码和输出。

## 核心数据结构

`review` 是 v1010 的核心结构：

- `review_ready`
  - 全部检查通过才为 `True`。
- `review_status`
  - pass 时为 `approved_for_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_lookup_only`。
- `receipt_index_path`
  - 被审阅的 v1009 index 路径。
- `receipt_index_row_count`
  - 必须为 1。
- `source_evidence_count`
  - 必须为 2。
- `lookup_keys`
  - 必须使用 receipt-index-receipt-index-receipt namespace。
- `promotion_ready`
  - 固定为 `False`。

## 核心检查

v1010 检查以下边界：

- v1009 index 文件必须存在。
- index 顶层 status/decision 必须 ready。
- index summary 与 body 必须 ready。
- lookup scope 与 granted use 必须是 downstream governance lookup only。
- lookup_ready 与 contract_check_ready 必须为 True。
- receipt index row 数量和 lookup key count 必须为 1。
- source evidence 必须有两行、状态 pass、SHA-256 格式合法、路径存在。
- source receipt/check 路径在 index body 和 row 中必须一致。
- source review 与 source receipt index 路径必须仍存在。
- consumer boundary 与 model quality claim 不能扩大。
- promotion 与 approved_for_promotion 必须为 False。
- source failed check count 必须为 0。
- source next step 必须从 v1009 指向 v1010 review。

## 运行证据

真实输出：

```text
e/1010/解释/review-v1010/
```

截图：

```text
e/1010/图片/v1010-review.png
```

真实运行摘要：

```text
status=pass
review_ready=True
receipt_index_row_count=1
source_evidence_count=2
lookup_key_count=1
receipt_index_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

## 一句话总结

v1010 把 v1009 receipt index 审阅成可继续 receipt recording 的 lookup-only 入口，同时保持模型能力声明和 promotion 边界不扩大。

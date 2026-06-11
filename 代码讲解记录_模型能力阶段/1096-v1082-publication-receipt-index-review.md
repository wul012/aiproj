# v1082 publication receipt index review

## 本版目标

v1082 的目标是 review v1081 receipt index。它不是新索引，也不是新 receipt，而是对 v1081 index 做只读审查，确认这份 index 可以作为下一步 receipt recording 的输入。

本版不做模型训练，不打开 promotion，不改变 v1081 的结论。

## 路线来源

v1081 已经把 v1079 receipt 和 v1080 contract check 合成 digest-backed index。v1082 站在下一步 receipt 之前，检查：

- index 是否 ready
- lookup key 是否仍然只有 1 条
- source evidence 是否完整
- contract check 是否 ready
- promotion 是否仍然关闭

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1082.py`
  - 核心 review builder。
  - 消费 v1081 index，输出 review summary、review body、check rows。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1082_artifacts.py`
  - 写出 JSON / CSV / TXT / MD / HTML 五种证据视图。

- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1082.py`
  - CLI 入口。
  - 支持 `--require-review-ready` 和 `--require-lookup-ready`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1082.py`
  - 覆盖 ready index、lookup-only 篡改、source evidence 缺失、source path 漂移和 CLI 输出。

## 数据流

```text
e/1081/解释/receipt-index-v1081
  -> review builder
  -> e/1082/解释/receipt-index-review-v1082
```

review 只读取 index，不重写 v1081 产物。

## 关键字段

- `review_ready=True`
  - 表示 v1081 index 通过只读审查。

- `review_status=...lookup_only`
  - 表示下一步只允许 lookup-only receipt recording。

- `source_evidence_count=2`
  - 表示 v1079 receipt 和 v1080 check 都仍在索引中。

- `promotion_ready=False`
  - 表示这条治理链仍不等于模型质量生产放行。

## 运行证据

运行截图在 `e/1082/图片/v1082-receipt-index-review.png`。

HTML 页面显示：

- `Status pass`
- `Review ready True`
- `Rows 1`
- `Lookup keys 1`
- `Evidence 2`
- `Failed 0`

## 验证

- focused v1082 tests：`5 passed in 0.65s`
- full pytest：`2801 passed in 629.07s`
- source hygiene：`2191/2191 clean`
- py_compile：新增模块、artifact writer、CLI、测试均通过。
- real CLI evidence：输出 JSON/CSV/TXT/MD/HTML sidecar。

## 一句话总结

v1082 把 v1081 receipt index 放进只读 review 闸门，确认下一步只能继续做 lookup-only receipt recording。

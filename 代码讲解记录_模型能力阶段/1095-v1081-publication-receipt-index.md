# v1081 publication receipt index

## 本版目标

v1081 的目标是把 v1079 receipt 和 v1080 contract check 编成一份新的 receipt index。

它解决的是下游消费便利性和证据完整性问题：后续 review 不需要自己重新找 receipt 和 check 的路径，也不需要猜测这两份文件是否仍然存在；v1081 index 直接把路径、摘要和 SHA-256 证据行放在一起。

本版不做模型训练，不提升模型能力声明，不打开 promotion。

## 路线来源

v1079 已经把 v1078 review 记录成 lookup-only receipt。v1080 已经证明 v1079 receipt 可以从源 review 重新推导且关键字段一致。v1081 则把这两份证据作为一组索引，交给下一版 review。

这条路线仍然是：

```text
review -> receipt -> contract check -> index -> review
```

v1081 处在 `contract check -> index` 这一段。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1081.py`
  - 核心 index builder。
  - 校验 receipt ready、lookup-only use、contract check ready、source path exists、no-promotion boundary。
  - 输出 `receipt_index_rows` 和 `source_evidence_rows`。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1081_artifacts.py`
  - 负责 JSON / CSV / TXT / MD / HTML 五种视图。
  - 这些都是同一份 index 的不同呈现，不是新的模型评测。

- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1081.py`
  - CLI 入口。
  - 读取 `--receipt` 与 `--receipt-check`，写出 `--out-dir`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1081.py`
  - 复用 v1077 同族测试结构。
  - 覆盖 ready path、granted use 篡改、contract check 未 ready、CLI sidecar 输出。

## 核心字段

- `index_ready`
  - v1081 自己的 ready 标志，只有 receipt 和 check 都通过时才为真。

- `lookup_scope`
  - 固定为 `downstream_governance_lookup_only`，说明这份 index 只能用于治理查阅。

- `lookup_key_count`
  - 当前仍然是 1，表示索引只承接一条 lookup row。

- `source_evidence_count`
  - 当前为 2，分别对应 v1079 receipt 和 v1080 check。

- `contract_check_ready`
  - 来自 v1080 check，必须为真。

- `promotion_ready`
  - 继续为 `False`。

## 输入输出

输入：

- `e/1079/解释/receipt-v1079/`
- `e/1080/解释/receipt-check-v1080/`

输出：

- `e/1081/解释/receipt-index-v1081/*.json`
- `e/1081/解释/receipt-index-v1081/*.csv`
- `e/1081/解释/receipt-index-v1081/*.txt`
- `e/1081/解释/receipt-index-v1081/*.md`
- `e/1081/解释/receipt-index-v1081/*.html`

## 测试覆盖

测试重点不是页面渲染，而是索引约束：

- 正常 receipt + check 能生成 `status=pass`。
- 篡改 `granted_use` 会失败，保护 lookup-only 边界。
- 将 contract check 改成未 ready 会失败，保护 check 作为前置门。
- CLI 能写出全部 sidecar，保护归档闭环。

## 运行证据

运行截图在 `e/1081/图片/v1081-receipt-index.png`。

HTML 页面展示了：

- `Status pass`
- `Index ready True`
- `Lookup keys 1`
- `Contract True`
- `Evidence 2`
- `Failed 0`

## 验证

- focused v1081 tests：`4 passed in 0.43s`
- full pytest：`2796 passed in 569.84s`
- source hygiene：`2187/2187 clean`
- py_compile：新增模块、artifact writer、CLI、测试均通过。
- real CLI evidence：输出 JSON/CSV/TXT/MD/HTML sidecar。

## 一句话总结

v1081 把 v1079 receipt 和 v1080 contract check 合成下一轮可消费的 lookup-only index，证据链继续保持只读、可追溯、不可 promotion。

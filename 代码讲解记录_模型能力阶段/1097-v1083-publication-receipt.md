# v1083 publication receipt

## 本版目标

v1083 的目标是把 v1082-reviewed receipt index 记录为一份新的 lookup-only receipt。

这一步解决的是下游契约输入问题：contract check 不应该直接消费 review，而是消费已经明确声明用途、consumer、source path 和 no-promotion 边界的 receipt。

本版不做模型训练，不声称模型能力提升，不放行 promotion。

## 路线来源

v1081 生成 receipt index，v1082 审核这份 index，v1083 把审核通过的 index 记录为 receipt。

```text
v1081 index -> v1082 review -> v1083 receipt
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1083.py`
  - 核心 receipt builder。
  - 校验 review ready、lookup-only use、source evidence、source path 和 next-step。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1083_artifacts.py`
  - 输出 JSON / CSV / TXT / MD / HTML。

- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1083.py`
  - CLI 入口。
  - 支持 `--require-receipt-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1083.py`
  - 覆盖 ready review、requested use 篡改、source evidence 缺失、review not ready、CLI 输出。

## 核心字段

- `receipt_ready=True`
  - 表示 v1083 receipt 可以被下一步 contract check 消费。

- `granted_use=downstream_governance_lookup_only`
  - 只允许治理查阅。

- `lookup_key_count=1`
  - 本轮仍然只承接一条 lookup key。

- `source_evidence_count=2`
  - 保持 v1079 receipt 和 v1080 check 两条 source evidence。

- `promotion_ready=False`
  - 明确不进入生产 promotion。

## 运行证据

运行截图在 `e/1083/图片/v1083-receipt.png`。

页面显示：

- `Status pass`
- `Receipt ready True`
- `Lookup keys 1`
- `Evidence 2`
- `Use downstream_governance_lookup_only`
- `Failed 0`

## 验证

- focused v1083 tests：`6 passed in 0.63s`
- full pytest：`2807 passed in 697.83s`
- source hygiene：`2195/2195 clean`
- py_compile：新增模块、artifact writer、CLI、测试均通过。
- real CLI evidence：输出 JSON/CSV/TXT/MD/HTML sidecar。

## 一句话总结

v1083 把 v1082 review 变成了可被 contract check 消费的 lookup-only receipt，继续保持证据链只读和不 promotion。

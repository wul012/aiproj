# v983 publication receipt

## 目标与边界

v983 的目标是把 v982 review 记录成一个 lookup-only receipt。v982 已经确认 v981 publication index 可以进入 receipt flow；v983 负责说明这个 index 被哪个消费者以什么用途接收。

本版不做模型训练，不改变 checkpoint，不做生产发布，也不扩展模型质量声明。它只是记录 receipt，边界仍然是：

- `granted_use=downstream_governance_lookup_only`
- `promotion_ready=False`
- `approved_for_promotion=False`

## 前置路线

1. v981 生成 publication index。
2. v982 review 该 index，确认 `receipt_ready=True`。
3. v983 记录 receipt，生成 consumer receipt row。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_v983.py`
  - 核心 receipt builder。
  - 输入 v982 review。
  - 校验 review ready、review status、requested use、blocked uses、source paths、lookup key namespace、no-promotion 和 next step。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_v983_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - 展示 receipt boundary、consumer receipt 和 checks。
- `scripts/record_randomized_holdout_publication_receipt_packet_index_publication_receipt_v983.py`
  - CLI 入口。
  - 支持 `--consumer-name`、`--requested-use`、`--require-receipt-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_v983.py`
  - 覆盖 ready receipt、requested use 越权、源 publication 缺失、CLI 失败码和 artifact 渲染。

## 核心数据结构

### `receipt`

`receipt` 是主产物：

- `receipt_ready=True`
- `receipt_id=randomized-holdout-publication-receipt-packet-index-publication-receipt-v983`
- `receipt_status=publication_index_lookup_receipted`
- `consumer_name=publication_registry_governance_lookup_reader`
- `requested_use=downstream_governance_lookup_only`
- `granted_use=downstream_governance_lookup_only`
- `lookup_keys`：来自 v982 review 的 `publication-index:` key。
- `blocked_uses`：继续保留 production/model/training claim 三类禁用用途。

### `consumer_receipts`

`consumer_receipts` 是给下游消费的简表：

- consumer
- lookup key
- publication id
- granted use
- blocked uses
- promotion ready
- receipt status

这让后续 receipt check 可以直接比较消费者接收内容，不必重新展开 v982 review。

## 20 条检查保护什么

v983 检查的重点是防止 receipt 越权：

1. v982 review 文件存在并 pass。
2. review decision 和 ready 字段正确。
3. review status 必须批准 lookup-only receipt。
4. requested use 必须是 downstream lookup only。
5. blocked uses 必须完整。
6. receipt/lookup/contract ready 均为 True。
7. index row 恰好 1 条，source evidence 恰好 2 条。
8. lookup key 必须使用 `publication-index:` namespace。
9. row 与 review 都不能 promotion。
10. source publication 和 source check 路径仍存在。
11. source failed check count 为 0。
12. next step 必须从 v982 review 指向 receipt。

## 运行证据

真实运行输出在：

```text
e/983/解释/publication-receipt-v983/
```

关键结果：

```text
status=pass
receipt_ready=True
granted_use=downstream_governance_lookup_only
lookup_key_count=1
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/983/图片/v983-randomized-holdout-publication-receipt-packet-index-publication-receipt.png
```

## 一句话总结

v983 把通过 v982 review 的 publication index 记录为 lookup-only receipt，让这条证据链从 review 进入可验收的消费者回执阶段。

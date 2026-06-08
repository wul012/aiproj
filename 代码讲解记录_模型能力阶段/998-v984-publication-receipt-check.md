# v984 publication receipt check

## 目标与边界

v984 的目标是检查 v983 receipt 是否能从 v982 review 重新构建。v983 已经记录 consumer receipt；v984 负责证明这个 receipt 没有被手写篡改，也没有把 lookup-only 用途扩大为 promotion。

本版不做模型训练，不改变 checkpoint，不做生产发布，也不扩展模型质量声明。

## 前置路线

1. v982 review publication index。
2. v983 根据 review 记录 receipt。
3. v984 从 v983 receipt 找回 v982 review，重建 receipt 并比较字段。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.py`
  - 核心 contract check builder。
  - 比较顶层 status/decision/failed_count、consumer receipts、summary 字段和 receipt 字段。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
- `scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_v984.py`
  - CLI 入口，支持 `--require-pass`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_check_v984.py`
  - 覆盖正常重建、granted use 篡改、源 review 缺失、CLI 失败码和输出渲染。

## 核心检查

v984 会比较：

- 顶层 `status`、`decision`、`failed_count`。
- `consumer_receipts`。
- `summary` 中的 receipt status、granted use、lookup key count、promotion、blocked uses、next step。
- `receipt` 中的 receipt ready、review id/status、source publication/check、no-promotion 和 next step。

这组比较保护的是 v983 receipt 的来源一致性。

## 运行证据

真实运行输出在：

```text
e/984/解释/publication-receipt-check-v984/
```

关键结果：

```text
status=pass
contract_check_ready=True
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
passed_check_count=39
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/984/图片/v984-randomized-holdout-publication-receipt-packet-index-publication-receipt-check.png
```

## 一句话总结

v984 把 v983 receipt 从“已记录”推进为“可由源 review 重建并通过 contract check 的 receipt”。

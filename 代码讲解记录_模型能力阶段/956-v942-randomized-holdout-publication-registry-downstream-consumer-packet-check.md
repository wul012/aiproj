# v942 randomized holdout publication registry downstream consumer packet check 代码讲解

## 本版目标和边界

v942 的目标是检查 v941 consumer packet 是否可由 v940 receipt review 重新构建：

```text
v940 downstream receipt review
  -> rebuild v941 consumer packet
  -> compare with v941 source packet
```

它回答的问题是：

```text
consumer packet 是否只是源 review 的稳定派生产物，而不是被手工改宽用途？
```

本版明确不做：

- 不重新训练模型。
- 不重新执行 randomized holdout replay。
- 不修改 v941 packet。
- 不批准 production promotion。

## 前置链路

v942 读取真实 v941 产物：

```text
e/941/解释/randomized-holdout-publication-registry-downstream-consumer-packet
```

v941 的关键结论是：

- `packet_status=downstream_consumer_packet_ready`
- `granted_use=downstream_governance_lookup_only`
- `lookup_ready=True`
- `promotion_ready=False`
- `next_step=check_randomized_holdout_publication_registry_downstream_consumer_packet`

v942 定位 v941 记录的 `receipt_review_path`，重新读取 v940 review 并调用 v941 builder 重建 packet。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_packet_check.py`

核心入口：

```python
build_randomized_holdout_publication_registry_downstream_consumer_packet_check(...)
```

输入：

- `consumer_packet_report`：v941 consumer packet JSON。
- `consumer_packet_path`：v941 JSON 路径，用于解析相对 source review。

输出结构：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
source_consumer_packet
source_receipt_review
source_summary
rebuilt_summary
source_packet
rebuilt_packet
source_packet_rows
rebuilt_packet_rows
check_rows
summary
interpretation
```

本版核心逻辑：

```text
source packet -> resolve receipt_review_path
receipt_review_path -> rebuild consumer packet
source vs rebuilt -> compare stable fields
```

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_packet_check_artifacts.py`

负责输出 JSON、CSV、TXT、Markdown 和 HTML。

JSON 是 contract check 的机器证据；CSV 列出所有检查行；TXT 适合命令行日志；Markdown 和 HTML 用于人工审阅与截图归档。

### `scripts/check_randomized_holdout_publication_registry_downstream_consumer_packet.py`

CLI 用法：

```powershell
python scripts\check_randomized_holdout_publication_registry_downstream_consumer_packet.py `
  e\941\解释\randomized-holdout-publication-registry-downstream-consumer-packet `
  --out-dir e\942\解释\randomized-holdout-publication-registry-downstream-consumer-packet-check `
  --require-pass `
  --force
```

## 核心检查

v942 有 37 个检查点，分为四类：

- source review 存在性：`source_receipt_review_present`、`source_receipt_review_exists`
- 顶层字段：`status`、`decision`、`failed_count`
- summary 字段：packet ready、status、consumer、lookup、granted use、blocked uses、promotion、boundary、claim、next step
- packet body 和 packet rows：lookup keys、source guard digest、packet rows 等稳定字段

这些检查保护：

- v941 packet 必须能定位到 v940 review。
- v941 packet 与重建 packet 的 lookup-only 边界一致。
- lookup key、blocked uses、source guard digest 不可漂移。
- promotion 相关字段必须保持 false。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_downstream_consumer_packet_check.py
```

覆盖场景：

- rebuildable packet 的 contract check 通过。
- packet lookup key 被篡改时失败。
- source receipt review 缺失时失败。
- CLI `--require-pass` 对篡改 packet 返回 `1`。
- artifact writer、locator、CLI、TXT/Markdown/HTML 渲染接通。

聚焦测试：

```text
9 passed
```

## 真实运行证据

真实 v941 输入生成 v942 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_packet_contract_check_passed
contract_check_ready=True
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=37
failed_check_count=0
```

证据目录：

```text
e/942/解释/randomized-holdout-publication-registry-downstream-consumer-packet-check
e/942/图片/v942-randomized-holdout-publication-registry-downstream-consumer-packet-check.png
```

## 链路角色

v942 是 consumer packet 的 contract check 层。它让后续 index 不直接信任 v941 packet，而是信任“可从 v940 review 重建且字段一致”的 packet。

## 一句话总结

v942 把 consumer packet 从“可消费”推进到“可重建验证”，增强了 downstream lookup 产物的防篡改能力。

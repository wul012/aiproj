# v935 randomized holdout publication registry lookup packet check 代码讲解

## 本版目标和边界

v935 的目标是给 v934 lookup packet 增加 contract check：

```text
v934 lookup packet
  -> v935 lookup packet contract check
```

它解决的问题是：

```text
lookup packet 是否仍能从 source manifest review 重新推导出来？
```

如果 lookup packet 被手工改了 key、删了 `production_promotion` 拒绝声明，或打开了 promotion 字段，v935 应该失败。

明确不做：

- 不重新训练。
- 不重新 replay。
- 不改写 v934 packet。
- 不把 check pass 解释成 production promotion。

## 前置链路

v935 消费真实 v934 产物：

```text
e/934/解释/randomized-holdout-publication-registry-lookup-packet
```

v934 packet 内记录了 source review：

```text
e/933/解释/randomized-holdout-publication-registry-manifest-review/randomized_holdout_publication_registry_manifest_review.json
```

v935 会读取该 review，重新调用 v934 builder，再比较原始 packet 与 rebuilt packet。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_lookup_packet_check.py`

核心入口：

```python
build_randomized_holdout_publication_registry_lookup_packet_check(...)
```

输入：

- `lookup_packet_report`：v934 lookup packet JSON。
- `lookup_packet_path`：lookup packet 文件路径。
- `title`：报告标题。
- `generated_at`：可选生成时间。

输出：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
source_lookup_packet
source_manifest_review
source_summary
rebuilt_summary
source_lookup_packet_body
rebuilt_lookup_packet_body
check_rows
summary
interpretation
```

### 重建逻辑

`_resolve_source_review(...)` 从两个位置找 source review：

```text
lookup_packet_report.registry_manifest_review_path
lookup_packet.lookup_packet.registry_manifest_review_path
```

找到后调用：

```python
build_randomized_holdout_publication_registry_lookup_packet(
    read_manifest_review_json(source_review),
    registry_manifest_review_path=source_review,
)
```

如果 source review 不存在，则生成一个 fail 状态的 rebuilt packet，使 check 明确失败。

### 对比字段

v935 对比 summary 字段：

```text
randomized_holdout_publication_registry_lookup_packet_ready
lookup_packet_id
lookup_scope
entry_count
lookup_ready
bounded_publication_accepted
promotion_ready
approved_for_promotion
consumer_boundary
allowed_use
rejected_use
next_step
```

也对比 lookup packet body：

```text
packet_ready
lookup_packet_id
lookup_scope
registry_manifest_review_path
entry_count
lookup_entries
lookup_keys
lookup_ready
bounded_publication_accepted
promotion_ready
approved_for_promotion
consumer_boundary
allowed_use
rejected_use
next_step
```

因此它能抓住：

- lookup key 被改。
- lookup entry 被改。
- `rejected_use=production_promotion` 被删。
- `promotion_ready` 被打开。
- source review 路径丢失。

### `src/minigpt/randomized_holdout_publication_registry_lookup_packet_check_artifacts.py`

负责输出 JSON/CSV/TXT/Markdown/HTML。CSV 写的是 check rows，便于定位哪个字段漂移。

### `scripts/check_randomized_holdout_publication_registry_lookup_packet.py`

CLI 用法：

```powershell
python scripts\check_randomized_holdout_publication_registry_lookup_packet.py `
  e\934\解释\randomized-holdout-publication-registry-lookup-packet `
  --out-dir e\935\解释\randomized-holdout-publication-registry-lookup-packet-check `
  --require-pass `
  --force
```

`--require-pass` 下任何字段不一致都会返回 1。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_lookup_packet_check.py
```

覆盖场景：

- rebuildable lookup packet check 通过。
- lookup key 被篡改时失败。
- source review 丢失时失败。
- CLI 在篡改 packet 上 `--require-pass` 返回 1。
- artifact writer、locator、CLI、TXT/Markdown/HTML 渲染全部接通。

聚焦测试：

```text
9 passed
```

## 真实运行证据

真实 v934 输入生成 v935 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_lookup_packet_contract_check_passed
contract_check_ready=True
original_lookup_scope=governance_lookup_only
rebuilt_lookup_scope=governance_lookup_only
original_rejected_use=production_promotion
rebuilt_rejected_use=production_promotion
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=32
failed_check_count=0
```

证据目录：

```text
e/935/解释/randomized-holdout-publication-registry-lookup-packet-check
e/935/图片/v935-randomized-holdout-publication-registry-lookup-packet-check.png
```

## 链路角色

v935 是 lookup packet 的防篡改层：

```text
manifest review
  -> lookup packet
  -> lookup packet contract check
```

它不扩大模型能力，只保证 lookup packet 仍能从 source review 推导，且 lookup-only / promotion=false 边界没有漂移。

## 一句话总结

v935 把 lookup packet 从“可查询产物”升级为“可重建校验产物”，让后续消费者更放心地使用 bounded randomized holdout publication lookup。

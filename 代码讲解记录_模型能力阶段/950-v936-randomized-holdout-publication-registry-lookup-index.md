# v936 randomized holdout publication registry lookup index 代码讲解

## 本版目标和边界

v936 的目标是把 v934 lookup packet 与 v935 contract check 合成一个 lookup index：

```text
v934 lookup packet
  + v935 lookup packet contract check
  -> v936 lookup index
```

它解决的问题是：

```text
后续消费者是否能在一个 artifact 中同时读取 lookup key、entry 摘要和 contract-check 状态？
```

回答是可以：

```text
randomized_holdout_publication_registry_lookup_index_ready
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不扩展模型质量结论。
- 不把 lookup index 解释为 production promotion。

## 前置链路

v936 消费两份真实产物：

```text
e/934/解释/randomized-holdout-publication-registry-lookup-packet
e/935/解释/randomized-holdout-publication-registry-lookup-packet-check
```

v934 提供 lookup key 和 entry；v935 证明 v934 可以从 v933 review 重建。v936 把这两层证据放进一个 index。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_lookup_index.py`

核心入口：

```python
build_randomized_holdout_publication_registry_lookup_index(...)
```

输入：

- `lookup_packet_report`：v934 lookup packet JSON。
- `lookup_packet_check_report`：v935 contract check JSON。
- `lookup_packet_path`：v934 路径。
- `lookup_packet_check_path`：v935 路径。

输出：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
lookup_packet_path
lookup_packet_check_path
source_lookup_packet_summary
source_lookup_packet_check_summary
lookup_entries
check_rows
lookup_index
summary
interpretation
```

`lookup_index` 是本版核心：

```text
index_ready
lookup_index_id
lookup_scope
lookup_packet_path
lookup_packet_check_path
entry_count
lookup_entries
lookup_keys
lookup_ready
contract_check_ready
bounded_publication_accepted
promotion_ready
approved_for_promotion
consumer_boundary
allowed_use
rejected_use
evidence_count
next_step
```

### `src/minigpt/randomized_holdout_publication_registry_lookup_index_artifacts.py`

负责输出：

- JSON：完整 index。
- CSV：lookup entries。
- TXT：CI 日志摘要。
- Markdown：归档阅读。
- HTML：截图和人工复核。

### `scripts/build_randomized_holdout_publication_registry_lookup_index.py`

CLI 用法：

```powershell
python scripts\build_randomized_holdout_publication_registry_lookup_index.py `
  --lookup-packet e\934\解释\randomized-holdout-publication-registry-lookup-packet `
  --lookup-packet-check e\935\解释\randomized-holdout-publication-registry-lookup-packet-check `
  --out-dir e\936\解释\randomized-holdout-publication-registry-lookup-index `
  --require-index-ready `
  --require-lookup-ready `
  --force
```

## 核心检查

v936 的检查点共 18 个：

```text
lookup_packet_file_exists
lookup_packet_check_file_exists
lookup_packet_passed
lookup_packet_decision_ready
lookup_packet_summary_ready
lookup_packet_check_passed
lookup_packet_check_decision_ready
contract_check_ready
lookup_keys_match_check
lookup_scope_governance
lookup_ready
entries_present
entries_not_promoted
consumer_boundary_governance
rejected_use_production_promotion
promotion_still_false
source_packet_checks_clean
source_contract_checks_clean
```

这些检查保护：

- packet 和 check 都真实存在。
- lookup key 与 contract check 一致。
- lookup scope 仍是 governance only。
- production promotion 仍被拒绝。
- entry 至少有一条，且没有 promotion。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_lookup_index.py
```

覆盖场景：

- 正常 packet + check 可以生成 ready index。
- contract check fail 时 index fail。
- lookup key 与 check 漂移时 index fail。
- artifact writer、locator、CLI、TXT/Markdown/HTML 渲染接通。

聚焦测试：

```text
9 passed
```

## 真实运行证据

真实 v934 + v935 输入生成 v936 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_lookup_index_ready
lookup_ready=True
contract_check_ready=True
promotion_ready=False
rejected_use=production_promotion
evidence_count=2
passed_check_count=18
failed_check_count=0
```

证据目录：

```text
e/936/解释/randomized-holdout-publication-registry-lookup-index
e/936/图片/v936-randomized-holdout-publication-registry-lookup-index.png
```

## 链路角色

v936 是 lookup 消费链的合并索引层：

```text
lookup packet
  -> lookup packet contract check
  -> lookup index
```

它让后续模块从一个 index 中读取可查询 key 和复核状态，而不是在多个 artifact 之间拼接。

## 一句话总结

v936 把 lookup packet 与 contract check 合并成稳定 lookup index，让 bounded randomized holdout publication 的查询入口更接近可维护的消费契约。

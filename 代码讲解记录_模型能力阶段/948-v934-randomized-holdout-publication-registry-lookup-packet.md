# v934 randomized holdout publication registry lookup packet 代码讲解

## 本版目标和边界

v934 的目标是把 v933 复核通过的 manifest review 转成 lookup packet：

```text
v933 publication registry manifest review
  -> v934 publication registry lookup packet
```

它解决的问题是：

```text
后续消费者如果只需要查询 bounded randomized holdout publication evidence，
能不能拿到一个稳定、只读、带 lookup key 的 packet？
```

回答是可以：

```text
randomized_holdout_publication_registry_lookup_packet_ready
```

明确不做：

- 不重新训练模型。
- 不重新 replay checkpoint。
- 不扩大模型质量结论。
- 不把 lookup packet 变成 production promotion 入口。

## 前置链路

v934 消费真实 v933 产物：

```text
e/933/解释/randomized-holdout-publication-registry-manifest-review
```

v933 已经把 v932 manifest 复核为：

```text
approved_for_governance_lookup_only
```

v934 在此基础上生成 lookup packet，把 entry 转成稳定 lookup key：

```text
publication:randomized-holdout-publication-v928
```

这个 key 用来支持后续查询，不代表模型上线或生产批准。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_lookup_packet.py`

核心入口：

```python
build_randomized_holdout_publication_registry_lookup_packet(...)
```

输入：

- `registry_manifest_review_report`：v933 review JSON。
- `registry_manifest_review_path`：review 文件路径。
- `title`：报告标题。
- `generated_at`：可选生成时间。

输出结构：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
registry_manifest_review_path
source_review_summary
source_review
entry_rows
check_rows
lookup_packet
summary
interpretation
```

其中 `lookup_packet` 是本版核心：

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

`lookup_entries` 中每条 entry 包含：

```text
lookup_key
entry_id
registry_status
bounded_publication_accepted
promotion_ready
consumer_boundary
allowed_use
model_quality_claim
random_seed
pass_rate
```

### `src/minigpt/randomized_holdout_publication_registry_lookup_packet_artifacts.py`

负责把 lookup packet 写成：

- JSON：完整结构，后续程序消费。
- CSV：lookup entry 表。
- TXT：CI 日志友好的 key-value。
- Markdown：归档阅读。
- HTML：Playwright 截图和人工审阅。

### `scripts/build_randomized_holdout_publication_registry_lookup_packet.py`

CLI 用法：

```powershell
python scripts\build_randomized_holdout_publication_registry_lookup_packet.py `
  --manifest-review e\933\解释\randomized-holdout-publication-registry-manifest-review `
  --out-dir e\934\解释\randomized-holdout-publication-registry-lookup-packet `
  --require-packet-ready `
  --require-lookup-ready `
  --force
```

`--require-promotion-ready` 当前应返回 1，因为本版明确拒绝 production promotion。

## 核心检查

v934 的检查点共 18 个：

```text
registry_manifest_review_file_exists
registry_manifest_review_passed
registry_manifest_review_decision_ready
review_summary_ready
review_status_lookup_only
lookup_ready
entry_count_positive
entries_registered
entries_bounded
entries_not_promoted
consumer_boundary_governance
model_quality_claim_bounded
allowed_use_lookup_only
rejected_use_production_promotion
promotion_still_false
approved_for_promotion_false
source_checks_clean
source_next_step_matches
```

这些检查保护三件事：

1. 输入 review 必须是 v933 ready 状态。
2. lookup packet 只能服务治理查询。
3. production promotion 必须继续被拒绝。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_lookup_packet.py
```

覆盖场景：

- lookup-only review 可以生成 ready packet。
- `lookup_ready=False` 时失败。
- `rejected_use` 被移除时失败。
- artifact writer、locator、CLI、TXT/Markdown/HTML 渲染都接通。

聚焦测试：

```text
8 passed
```

## 真实运行证据

真实 v933 输入生成 v934 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_lookup_packet_ready
lookup_scope=governance_lookup_only
lookup_ready=True
promotion_ready=False
rejected_use=production_promotion
passed_check_count=18
failed_check_count=0
```

证据目录：

```text
e/934/解释/randomized-holdout-publication-registry-lookup-packet
e/934/图片/v934-randomized-holdout-publication-registry-lookup-packet.png
```

## 链路角色

v934 是 lookup 消费前的 packet 层：

```text
registry manifest
  -> manifest review
  -> lookup packet
  -> lookup packet check
```

它让后续消费者不用理解整条 v925-v933 证据链，也能通过稳定 key 查到 bounded publication evidence。

## 一句话总结

v934 把 lookup-only review 转成稳定 lookup packet，同时用 18 个检查点守住 bounded claim 和 production promotion=false。

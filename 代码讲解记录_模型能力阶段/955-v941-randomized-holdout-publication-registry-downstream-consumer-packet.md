# v941 randomized holdout publication registry downstream consumer packet 代码讲解

## 本版目标和边界

v941 的目标是把 v940 receipt review 转成 downstream consumer packet：

```text
v940 downstream receipt review
  -> v941 downstream consumer packet
```

v940 已经审核 receipt 可进入 consumer packet。v941 负责生成真正给下游模块读取的稳定包。

本版明确不做：

- 不重新训练模型。
- 不重新执行 randomized holdout replay。
- 不修改上游 review。
- 不批准 production promotion。

## 维护性改进

本版新增：

```text
src/minigpt/randomized_holdout_publication_downstream_common.py
```

它集中承接 downstream lookup 相关 helper：

```text
downstream_lookup_use()
blocked_uses()
blocked_uses_complete(...)
is_downstream_lookup_only(...)
is_sha256(...)
sha256_file(...)
```

这样 v941 后续版本不需要继续复制 blocked uses、lookup-only 和 SHA-256 判断。`randomized_holdout_publication_constants.py` 也新增了共享的 downstream lookup use、blocked uses 和 consumer packet next step。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_packet.py`

核心入口：

```python
build_randomized_holdout_publication_registry_downstream_consumer_packet(...)
```

输入：

- `receipt_review_report`：v940 receipt review JSON。
- `receipt_review_path`：v940 JSON 路径，用于检查源文件存在。

输出结构：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
receipt_review_path
source_receipt_review_summary
source_receipt_review
consumer_receipts
entry_rows
packet_rows
check_rows
packet
summary
interpretation
```

`packet` 是本版核心结构：

```text
packet_ready
packet_id
packet_status
receipt_review_path
consumer_name
consumer_boundary
granted_use
blocked_uses
entry_count
consumer_receipt_count
lookup_keys
source_guard_sha256
promotion_ready
approved_for_promotion
model_quality_claim
next_step
```

`packet_rows` 是给下游消费的行级视图，按 consumer receipt 展开 lookup key 和 entry id。

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_packet_artifacts.py`

负责输出 JSON、CSV、TXT、Markdown 和 HTML。

JSON 是机器消费证据；CSV 是 packet rows；TXT 适合命令行日志；Markdown/HTML 用于人工审阅和截图归档。

### `scripts/build_randomized_holdout_publication_registry_downstream_consumer_packet.py`

CLI 用法：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_packet.py `
  --receipt-review e\940\解释\randomized-holdout-publication-registry-downstream-receipt-review `
  --out-dir e\941\解释\randomized-holdout-publication-registry-downstream-consumer-packet `
  --require-packet-ready `
  --require-lookup-ready `
  --force
```

## 核心检查

v941 有 20 个检查点：

```text
receipt_review_file_exists
receipt_review_passed
receipt_review_decision_ready
review_summary_ready
review_status_packet_ready
consumer_ready
granted_use_lookup_only
blocked_uses_complete
promotion_still_false
approved_for_promotion_false
consumer_boundary_governance
model_quality_claim_bounded
source_guard_digest_shape
consumer_receipts_present
entries_present
consumer_receipts_lookup_only
consumer_receipts_not_promoted
lookup_keys_publication_namespace
source_checks_clean
source_next_step_matches
```

这些检查保护：

- v940 review 必须真实存在并通过。
- packet 只能授予 downstream governance lookup。
- blocked uses 必须完整。
- lookup key 必须使用 `publication:` namespace。
- promotion 相关字段必须保持 false。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_downstream_consumer_packet.py
```

覆盖场景：

- ready review 可以生成 packet ready 的 v941 包。
- review 的 granted use 扩张为 `production_promotion` 时失败。
- lookup key namespace 漂移时失败。
- artifact writer、locator、CLI、TXT/Markdown/HTML 渲染接通。
- 前序 guard/receipt/review 测试与新 helper 一起通过。

聚焦测试：

```text
16 passed
```

## 真实运行证据

真实 v940 输入生成 v941 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_packet_ready
packet_status=downstream_consumer_packet_ready
lookup_ready=True
granted_use=downstream_governance_lookup_only
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

证据目录：

```text
e/941/解释/randomized-holdout-publication-registry-downstream-consumer-packet
e/941/图片/v941-randomized-holdout-publication-registry-downstream-consumer-packet.png
```

## 链路角色

v941 是 receipt review 后的消费包层。它让后续模块读取一个稳定 packet，而不是直接解析多层 review/receipt/guard。

## 一句话总结

v941 把下游治理查阅能力从“已复核”推进到“可包化消费”，同时用公共 helper 收束重复边界判断。

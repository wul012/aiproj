# v940 randomized holdout publication registry downstream receipt review 代码讲解

## 本版目标和边界

v940 的目标是 review v939 downstream receipt：

```text
v939 downstream receipt
  -> v940 downstream receipt review
```

v939 已经记录消费者、授予用途、blocked uses 和 source guard digest。v940 负责确认这份 receipt 可以进入后续 consumer packet 构建。

本版明确不做：

- 不重新训练模型。
- 不重新执行 randomized holdout replay。
- 不修改上游 receipt 或 guard。
- 不把下游查阅收据升级成生产晋级许可。

## 前置链路

v940 读取真实 v939 产物：

```text
e/939/解释/randomized-holdout-publication-registry-downstream-receipt
```

v939 的关键结论是：

- `receipt_status=downstream_governance_lookup_receipted`
- `granted_use=downstream_governance_lookup_only`
- `blocked_uses=[production_promotion, model_quality_expansion, training_data_claim_expansion]`
- `promotion_ready=False`
- `downstream_guard_sha256` 指向 v938 source guard

v940 只复核这些事实，不扩大结论边界。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_downstream_receipt_review.py`

核心入口：

```python
build_randomized_holdout_publication_registry_downstream_receipt_review(...)
```

输入：

- `receipt_report`：v939 receipt JSON。
- `downstream_receipt_path`：v939 JSON 路径，用于检查 receipt 文件存在。

输出结构：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
downstream_receipt_path
source_downstream_receipt_summary
source_downstream_receipt
source_downstream_guard_sha256
consumer_receipts
entry_rows
check_rows
review
summary
interpretation
```

`review` 是本版核心结构：

```text
review_ready
review_id
review_status
downstream_receipt_path
consumer_name
consumer_ready
entry_count
granted_use
blocked_uses
source_guard_sha256
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
next_step
```

其中 `source_guard_sha256` 来自 v939 receipt，并由检查逻辑重新读取 v938 guard 文件计算摘要做比对。

### `src/minigpt/randomized_holdout_publication_registry_downstream_receipt_review_artifacts.py`

负责输出 JSON、CSV、TXT、Markdown 和 HTML。

JSON 是机器消费证据；CSV 保留 consumer receipt rows；TXT 适合命令行日志；Markdown 和 HTML 用于人工审阅、截图和归档。

HTML 页面突出展示：

- status / review ready / consumer / granted use / promotion / failed
- blocked uses
- source guard digest
- next step
- consumer receipt rows
- 20 条检查

### `scripts/review_randomized_holdout_publication_registry_downstream_receipt.py`

CLI 用法：

```powershell
python scripts\review_randomized_holdout_publication_registry_downstream_receipt.py `
  --receipt e\939\解释\randomized-holdout-publication-registry-downstream-receipt `
  --out-dir e\940\解释\randomized-holdout-publication-registry-downstream-receipt-review `
  --require-review-ready `
  --require-consumer-ready `
  --force
```

如果传 `--require-promotion-ready`，当前应失败，因为 v940 明确不批准 promotion。

## 核心检查

v940 有 20 个检查点：

```text
downstream_receipt_file_exists
downstream_receipt_passed
downstream_receipt_decision_ready
receipt_summary_ready
receipt_status_ready
granted_use_lookup_only
blocked_uses_complete
promotion_still_false
approved_for_promotion_false
consumer_boundary_governance
model_quality_claim_bounded
consumer_receipts_present
consumer_receipts_lookup_only
consumer_receipts_not_promoted
entries_present
lookup_key_count_matches
source_guard_digest_shape
source_guard_digest_matches
source_checks_clean
source_next_step_matches
```

这些检查保护四个关键边界：

- v939 receipt 必须真实存在并通过。
- receipt 授予用途必须仍是 downstream governance lookup only。
- source guard digest 必须能从 v938 文件重新计算出来。
- promotion 和 approved_for_promotion 必须保持 false。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_downstream_receipt_review.py
```

覆盖场景：

- ready receipt 可以生成 review ready 的 v940 审核结果。
- source guard digest 被篡改时失败。
- granted use 扩张为 `production_promotion` 时失败。
- artifact writer、locator、CLI、TXT/Markdown/HTML 渲染接通。
- `require_promotion_ready=True` 必须返回失败。

聚焦测试：

```text
8 passed
```

## 真实运行证据

真实 v939 输入生成 v940 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_receipt_review_ready
review_status=approved_for_downstream_consumer_packet
consumer_ready=True
granted_use=downstream_governance_lookup_only
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

证据目录：

```text
e/940/解释/randomized-holdout-publication-registry-downstream-receipt-review
e/940/图片/v940-randomized-holdout-publication-registry-downstream-receipt-review.png
```

## 链路角色

v940 是 consumer packet 之前的审核层。它确保后续 packet 不需要直接信任 v939 receipt，而是可以读取一份已复核的 receipt review。

## 一句话总结

v940 把下游 receipt 从“已记录”推进到“已复核可消费”，让后续 consumer packet 只能在治理查阅边界内继续构建。

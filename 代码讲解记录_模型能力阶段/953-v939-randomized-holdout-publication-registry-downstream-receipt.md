# v939 randomized holdout publication registry downstream receipt 代码讲解

## 本版目标和边界

v939 的目标是把 v938 downstream guard 转成一份可复核 receipt：

```text
v938 downstream guard
  -> v939 downstream receipt
```

v938 已经明确 allowed use 和 blocked uses。v939 进一步回答：

```text
哪个消费者可以读取 lookup index？读取用途是什么？哪些用途仍然禁止？
```

本版明确不做：

- 不重新训练模型。
- 不重新执行 randomized holdout replay。
- 不修改 v938 源 guard。
- 不把 receipt 当作 production promotion 许可。

## 前置链路

v939 读取真实 v938 产物：

```text
e/938/解释/randomized-holdout-publication-registry-downstream-guard
```

v938 的关键结论是：

- `guard_status=downstream_governance_lookup_allowed`
- `allowed_use=downstream_governance_lookup_only`
- `blocked_uses=[production_promotion, model_quality_expansion, training_data_claim_expansion]`
- `promotion_ready=False`
- `next_step=record_randomized_holdout_publication_registry_downstream_receipt`

v939 不放宽这些边界，只把它们写成面向消费者的收据。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_downstream_receipt.py`

核心入口：

```python
build_randomized_holdout_publication_registry_downstream_receipt(...)
```

输入：

- `downstream_guard_report`：v938 downstream guard JSON。
- `downstream_guard_path`：v938 JSON 路径，用于文件存在检查和 SHA-256 摘要。
- `consumer_name`：下游消费者名称。
- `requested_use`：请求用途，默认只能是 `downstream_governance_lookup_only`。

输出结构：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
downstream_guard_path
downstream_guard_sha256
source_downstream_guard_summary
source_downstream_guard
entry_rows
consumer_receipts
check_rows
receipt
summary
interpretation
```

`receipt` 是本版核心数据结构：

```text
receipt_ready
receipt_id
receipt_type
receipt_status
consumer_name
requested_use
granted_use
downstream_guard_path
entry_count
lookup_keys
guard_id
guard_status
blocked_uses
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
next_step
```

最关键的是：

- `granted_use=downstream_governance_lookup_only`
- `promotion_ready=False`
- `approved_for_promotion=False`
- `blocked_uses` 必须保留三项禁用用途

此外，`downstream_guard_sha256` 记录 v938 源 JSON 摘要，方便后续确认 receipt 是否来自同一份 guard。

### `src/minigpt/randomized_holdout_publication_registry_downstream_receipt_artifacts.py`

负责输出 JSON、CSV、TXT、Markdown 和 HTML。

JSON 是最终机器证据；CSV 记录 consumer receipts；TXT 适合命令行/CI；Markdown 和 HTML 用于人工审阅与截图归档。

HTML 页面展示：

- status / receipt ready / consumer / granted use / promotion / failed
- blocked uses
- next step
- source digest
- consumer receipts
- 18 条检查

### `scripts/build_randomized_holdout_publication_registry_downstream_receipt.py`

CLI 用法：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_receipt.py `
  --guard e\938\解释\randomized-holdout-publication-registry-downstream-guard `
  --out-dir e\939\解释\randomized-holdout-publication-registry-downstream-receipt `
  --require-receipt-ready `
  --force
```

`--requested-use production_promotion` 会失败，因为 receipt 不能把 downstream lookup 升级成 promotion 权限。

## 核心检查

v939 有 18 个检查点：

```text
downstream_guard_file_exists
downstream_guard_passed
downstream_guard_decision_ready
guard_summary_ready
guard_status_allowed
requested_use_allowed
blocked_uses_complete
promotion_still_false
approved_for_promotion_false
downstream_lookup_ready
contract_check_ready
consumer_boundary_governance
model_quality_claim_bounded
entries_present
lookup_keys_publication_namespace
entries_not_promoted
source_checks_clean
source_next_step_matches
```

这些检查保护四件事：

- v938 guard 必须真实存在并通过。
- receipt 请求用途必须保持 downstream governance lookup only。
- production promotion 和 approved_for_promotion 必须保持 false。
- lookup key、entry count 和 source next step 必须与上游一致。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_downstream_receipt.py
```

覆盖场景：

- ready guard 可以生成 receipt ready 的 v939 收据。
- 缺少 blocked use 时失败。
- 请求 `production_promotion` 时失败。
- source guard SHA-256 为 64 位摘要。
- artifact writer、locator、CLI、TXT/Markdown/HTML 渲染接通。
- `require_promotion_ready=True` 必须返回失败。

聚焦测试：

```text
8 passed
```

## 真实运行证据

真实 v938 输入生成 v939 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_receipt_ready
receipt_status=downstream_governance_lookup_receipted
granted_use=downstream_governance_lookup_only
promotion_ready=False
blocked_uses=['production_promotion', 'model_quality_expansion', 'training_data_claim_expansion']
passed_check_count=18
failed_check_count=0
```

证据目录：

```text
e/939/解释/randomized-holdout-publication-registry-downstream-receipt
e/939/图片/v939-randomized-holdout-publication-registry-downstream-receipt.png
```

## 链路角色

v939 是下游消费的收据层。它不是新训练证据，而是把 v938 的 guard 变成更适合后续模块读取的消费契约。

后续如果要继续推进，应先 review 这份 receipt，而不是直接基于 lookup index 扩展模型能力结论。

## 一句话总结

v939 把“可以下游治理查阅”落实成带消费者、用途、禁用项和源摘要的 receipt，让随机 holdout 发布登记结果具备更清楚的下游消费契约。

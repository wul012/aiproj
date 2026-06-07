# v953 randomized holdout publication registry downstream consumer ack bundle publication receipt

## 本版目标与边界

v953 的目标是记录 downstream consumer 对 v952 publication index review 的接收回执。v952 已经审核 index 可供 lookup-only 消费；v953 则把消费方、granted use、blocked uses、lookup key 和 source review digest 固化成 receipt。

这版不训练模型，不批准生产上线，不扩大模型质量声称。它只确认下游获得的是 governance lookup 权限。

前置链路：

```text
v951 publication index
 -> v952 publication index review
 -> v953 downstream publication receipt
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt.py`
  - v953 核心 receipt builder。
  - 读取 v952 review，检查 requested use、blocked uses、publication rows、source evidence counts、source publication/check 文件和 no-promotion 字段。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 输出 consumer receipt row。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt.py`
  - v953 CLI。
  - 支持 `--require-receipt-ready` 和 `--require-promotion-ready`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt.py`
  - 覆盖 ready receipt、promotion request 拒绝、publication row 缺失、CLI 和 artifact 输出。

- `e/953/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt/`
  - 使用真实 v952 review 生成的运行证据。

## 核心数据结构

`receipt` 是本版主结构：

```python
{
    "receipt_ready": True,
    "receipt_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-v953",
    "receipt_status": "downstream_publication_lookup_receipted",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "requested_use": "downstream_governance_lookup_only",
    "granted_use": "downstream_governance_lookup_only",
    "publication_row_count": 1,
    "source_evidence_count": 2,
    "blocked_uses": [
        "production_promotion",
        "model_quality_expansion",
        "training_data_claim_expansion",
    ],
    "promotion_ready": False,
    "next_step": "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt",
}
```

`index_review_sha256` 是对 v952 review JSON 的文件 digest，用来证明 receipt 引用的是当前 review 文件。

## 核心检查逻辑

`_checks()` 生成 20 条检查：

- `index_review_file_exists`：v952 review 文件必须存在。
- `index_review_passed` 与 `index_review_decision_ready`：v952 必须通过。
- `index_review_summary_ready`：summary 与 review body 必须 ready。
- `review_status_allowed`：review 只批准 downstream publication lookup。
- `requested_use_allowed`：请求用途必须是 `downstream_governance_lookup_only`。
- `blocked_uses_complete`：三类阻断用途必须完整保留。
- `downstream_lookup_ready` 与 `contract_check_ready`：下游 lookup 和 contract check 必须 ready。
- `publication_rows_present` 与 `source_evidence_count`：必须有 1 条 publication row、2 条 source evidence。
- `lookup_keys_publication_namespace`：lookup key 必须属于 `publication:` 命名空间。
- `publication_rows_not_promoted`：publication row 不得 promotion。
- `promotion_still_false`：summary、review、approved_for_promotion 都不能打开。
- `consumer_boundary_governance` 与 `model_quality_claim_bounded`：消费边界和模型声称必须保守。
- `source_publication_file_exists` 与 `source_publication_check_file_exists`：源 publication 和 contract check 必须仍存在。
- `source_checks_clean` 和 `source_next_step_matches`：v952 源检查必须 clean，且路由到本版 receipt。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt.py --index-review e\952\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-index-review --out-dir e\953\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt --require-receipt-ready --force
```

流程：

1. 定位 v952 publication index review JSON。
2. 读取 review report。
3. 检查 lookup-only use、blocked uses、publication row、source evidence 和 source artifact。
4. 计算 index review SHA-256。
5. 输出 receipt JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 4 个场景：

- ready index review 可以生成 ready receipt。
- requested use 为 production promotion 时失败。
- publication row 缺失时失败。
- CLI 和 artifact writer 输出完整。

这组测试保护下游消费权限不会在 receipt 层被扩大。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_ready
failed_count=0
receipt_status=downstream_publication_lookup_receipted
granted_use=downstream_governance_lookup_only
publication_row_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

Playwright MCP 截图：

```text
e/953/图片/v953-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt.png
```

## 一句话总结

v953 把 v952 lookup-only index review 固化为 downstream receipt，明确下游只获得治理查阅权限。

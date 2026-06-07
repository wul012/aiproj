# v954 randomized holdout publication registry downstream consumer ack bundle publication receipt review

## 本版目标与边界

v954 的目标是审核 v953 downstream publication receipt。v953 已经把 v952 publication index review 固化成 receipt；v954 则确认这个 receipt 可以进入下一步 receipt packet 构建。

这版不训练模型，不修改 benchmark，不批准生产上线，也不扩大模型质量声称。它只做 receipt review：确认 receipt 与源 index review、source publication、source publication check 仍然一致，并且下游消费仍然是 governance lookup only。

前置链路：

```text
v952 publication index review
 -> v953 downstream publication receipt
 -> v954 publication receipt review
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review.py`
  - v954 核心 review builder。
  - 读取 v953 receipt，检查 receipt readiness、receipt status、granted use、blocked uses、publication rows、source evidence rows、source digest、source artifact 和 no-promotion 字段。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 仍输出 consumer receipt row；HTML 展示 review boundary 和全部检查。

- `scripts/review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt.py`
  - v954 CLI。
  - 支持 `--require-review-ready`、`--require-packet-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review.py`
  - 覆盖 ready review、granted use 扩张拒绝、source digest 漂移拒绝、source index review 缺失拒绝、CLI 和 artifact 输出。

- `e/954/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-review/`
  - 使用真实 v953 receipt 生成的运行证据。

## 核心数据结构

`review` 是本版主结构：

```python
{
    "review_ready": True,
    "review_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-review-v954",
    "review_status": "approved_for_downstream_publication_receipt_packet",
    "publication_receipt_sha256": "...",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "packet_ready": True,
    "receipt_status": "downstream_publication_lookup_receipted",
    "granted_use": "downstream_governance_lookup_only",
    "publication_row_count": 1,
    "source_evidence_count": 2,
    "lookup_keys": ["publication:..."],
    "blocked_uses": [
        "production_promotion",
        "model_quality_expansion",
        "training_data_claim_expansion",
    ],
    "promotion_ready": False,
    "approved_for_promotion": False,
    "next_step": "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet",
}
```

`publication_receipt_sha256` 是对 v953 receipt JSON 的 digest。`index_review_sha256` 仍来自 v953 receipt，并在 v954 中重新与 `source_index_review_path` 指向的文件比对，避免 receipt 引用的 source review 漂移。

## 核心检查逻辑

`_checks()` 生成 24 条检查：

- `publication_receipt_file_exists`：v953 receipt 文件必须存在。
- `publication_receipt_passed` 与 `publication_receipt_decision_ready`：v953 receipt 必须通过。
- `receipt_summary_ready`：summary 和 receipt body 都必须 ready。
- `receipt_status_ready`：receipt status 必须是 `downstream_publication_lookup_receipted`。
- `granted_use_lookup_only`：summary 与 body 都只能是 `downstream_governance_lookup_only`。
- `blocked_uses_complete`：三类 blocked uses 必须完整保留。
- `publication_rows_present`、`source_evidence_rows_present`、`consumer_receipts_present`：行数必须分别是 1、2、1。
- `lookup_keys_publication_namespace`：lookup key 必须属于 `publication:` 命名空间。
- `consumer_receipts_lookup_only`：consumer receipt 行不能扩张用途。
- `publication_rows_not_promoted` 与 `consumer_receipts_not_promoted`：所有行都不得 promotion。
- `promotion_still_false`：summary、receipt、approved_for_promotion 都不能打开。
- `consumer_boundary_governance` 与 `model_quality_claim_bounded`：消费边界和模型声称必须保持保守。
- `source_index_review_file_exists`、`source_publication_file_exists`、`source_publication_check_file_exists`：上游源文件必须仍存在。
- `source_index_review_digest_shape` 与 `source_index_review_digest_matches`：source review digest 必须是合法 sha256，并与文件内容一致。
- `source_checks_clean` 与 `source_next_step_matches`：v953 源检查必须 clean，且路由到本版 review。

## CLI 运行流程

真实命令：

```powershell
python scripts\review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt.py --receipt e\953\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt --out-dir e\954\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-review --require-review-ready --require-packet-ready --force
```

流程：

1. 定位 v953 publication receipt JSON。
2. 读取 receipt report。
3. 检查 receipt status、granted use、blocked uses、publication rows、source evidence rows 和 source artifact。
4. 重新计算 v953 receipt sha256 和 v952 index review sha256。
5. 输出 review JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 5 个场景：

- ready publication receipt 可以生成 ready review。
- granted use 被改成 production promotion 时失败。
- source index review digest 漂移时失败。
- source index review 文件消失时失败。
- CLI 和 artifact writer 输出完整。

这组测试保护 receipt review 不会把 lookup-only receipt 升级成生产权限，也保护 source review 关系不会被静默篡改。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_review_ready
failed_count=0
review_status=approved_for_downstream_publication_receipt_packet
packet_ready=True
receipt_status=downstream_publication_lookup_receipted
granted_use=downstream_governance_lookup_only
publication_row_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=24
failed_check_count=0
```

Playwright MCP 截图：

```text
e/954/图片/v954-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-review.png
```

## 一句话总结

v954 把 v953 lookup-only downstream publication receipt 审核成可打包的 receipt review，同时继续阻断 promotion 和模型质量声称扩张。

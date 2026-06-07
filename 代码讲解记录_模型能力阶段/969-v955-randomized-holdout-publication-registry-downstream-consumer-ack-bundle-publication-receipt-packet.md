# v955 randomized holdout publication registry downstream consumer ack bundle publication receipt packet

## 本版目标与边界

v955 的目标是把 v954 publication receipt review 打包成 receipt packet。v954 已经确认 v953 receipt 仍然 lookup-only、source digest 未漂移、source artifacts 仍存在；v955 则把这些审核结果整理成下一步 contract check 能消费的稳定 packet。

这版不训练模型，不新增 benchmark，不批准 promotion。它只是把 review 的结论、consumer receipt row、publication row、source evidence row 和 digest 字段放到一个 packet 产物里。

前置链路：

```text
v953 downstream publication receipt
 -> v954 publication receipt review
 -> v955 publication receipt packet
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.py`
  - v955 核心 packet builder。
  - 读取 v954 review，检查 review readiness、review status、packet readiness、granted use、blocked uses、row counts、source artifacts、digest shape 和 no-promotion 字段。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 输出 packet row，HTML 展示 packet boundary 和全部检查。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.py`
  - v955 CLI。
  - 支持 `--require-packet-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.py`
  - 覆盖 ready packet、granted use 扩张拒绝、lookup key 命名空间漂移拒绝、source publication 缺失拒绝、CLI 和 artifact 输出。

- `e/955/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet/`
  - 使用真实 v954 review 生成的运行证据。

## 核心数据结构

`packet` 是本版主结构：

```python
{
    "packet_ready": True,
    "packet_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-v955",
    "packet_status": "downstream_publication_receipt_packet_ready",
    "receipt_review_sha256": "...",
    "publication_receipt_sha256": "...",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "granted_use": "downstream_governance_lookup_only",
    "publication_row_count": 1,
    "source_evidence_count": 2,
    "consumer_receipt_count": 1,
    "lookup_keys": ["publication:..."],
    "blocked_uses": [
        "production_promotion",
        "model_quality_expansion",
        "training_data_claim_expansion",
    ],
    "promotion_ready": False,
    "approved_for_promotion": False,
    "next_step": "check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet",
}
```

`packet_rows` 是供 CSV、HTML 和后续 check 使用的扁平行结构。它保留 packet id、consumer、lookup key、publication id、granted use、receipt status 和 packet status。

## 核心检查逻辑

`_checks()` 生成 27 条检查：

- `receipt_review_file_exists`：v954 review 文件必须存在。
- `receipt_review_passed` 与 `receipt_review_decision_ready`：v954 review 必须通过。
- `review_summary_ready`：summary 和 review body 都必须 ready。
- `review_status_packet_ready` 与 `packet_ready`：review 只能批准 receipt packet 构建。
- `receipt_status_ready`：源 receipt 仍必须是 `downstream_publication_lookup_receipted`。
- `granted_use_lookup_only`：summary 与 review body 都只能是 lookup-only。
- `blocked_uses_complete`：三类 blocked uses 必须完整保留。
- `publication_rows_present`、`source_evidence_rows_present`、`consumer_receipts_present`：行数必须分别是 1、2、1。
- `lookup_keys_publication_namespace`：lookup key 必须属于 `publication:` 命名空间。
- `consumer_receipts_lookup_only`、`consumer_receipts_not_promoted`、`publication_rows_not_promoted`：消费和 publication 行都不得 promotion。
- `receipt_review_digest_shape` 和 `publication_receipt_digest_shape`：digest 字段必须是合法 sha256。
- `source_index_review_file_exists`、`source_publication_file_exists`、`source_publication_check_file_exists`：源 artifacts 必须仍存在。
- `promotion_still_false` 与 `approved_for_promotion_false`：packet 不允许打开 promotion。
- `consumer_boundary_governance` 与 `model_quality_claim_bounded`：消费边界和模型声称必须保守。
- `source_checks_clean` 与 `source_next_step_matches`：v954 源检查必须 clean，且路由到本版 packet。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.py --receipt-review e\954\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-review --out-dir e\955\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet --require-packet-ready --require-lookup-ready --force
```

流程：

1. 定位 v954 receipt review JSON。
2. 读取 review report。
3. 检查 lookup-only、blocked uses、row counts、source artifacts、digest shape 和 no-promotion 字段。
4. 计算 v954 review sha256。
5. 输出 packet JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 5 个场景：

- ready review 可以生成 ready packet。
- granted use 被改成 production promotion 时失败。
- lookup key 从 `publication:` 漂移到 `model:` 时失败。
- source publication 文件消失时失败。
- CLI 和 artifact writer 输出完整。

这组测试保护 packet 不会把 receipt review 变成权限升级，也保护后续 contract check 能拿到稳定输入。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_ready
failed_count=0
packet_status=downstream_publication_receipt_packet_ready
lookup_ready=True
granted_use=downstream_governance_lookup_only
publication_row_count=1
source_evidence_count=2
consumer_receipt_count=1
promotion_ready=False
passed_check_count=27
failed_check_count=0
```

Playwright MCP 截图：

```text
e/955/图片/v955-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet.png
```

## 一句话总结

v955 把 v954 receipt review 打包成可复核的 receipt packet，为下一步 contract check 提供稳定输入，同时继续阻断 promotion 和模型质量声称扩张。

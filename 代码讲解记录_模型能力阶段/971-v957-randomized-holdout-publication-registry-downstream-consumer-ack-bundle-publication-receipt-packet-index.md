# v957 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index

## 本版目标与边界

v957 的目标是把 v955 receipt packet 和 v956 receipt packet contract check 合并成 lookup-only index。v955 提供 packet，v956 证明 packet 可重建；v957 负责把这两个产物整理成后续 index review 的稳定输入。

这版不训练模型，不生成新的质量结论，不批准 promotion。它只是索引：只有 packet 与 contract check 都 clean，才输出一条 packet index row。

前置链路：

```text
v955 publication receipt packet
 -> v956 publication receipt packet contract check
 -> v957 publication receipt packet index
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.py`
  - v957 核心 index builder。
  - 同时读取 v955 packet 与 v956 check，检查 packet ready、contract check ready、granted use、lookup key、source evidence、source artifacts 和 no-promotion 字段。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 输出 packet index row，HTML 展示 lookup boundary、source evidence 和全部检查。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.py`
  - v957 CLI。
  - 支持 `--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.py`
  - 覆盖 ready index、contract check 失败、granted use 漂移、CLI 失败退出和 artifact 输出。

- `e/957/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index/`
  - 使用真实 v955 packet 与 v956 check 生成的运行证据。

## 核心数据结构

`packet_index` 是本版主结构：

```python
{
    "index_ready": True,
    "packet_index_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-v957",
    "lookup_scope": "downstream_governance_lookup_only",
    "packet_index_rows": [
        {
            "lookup_key": "publication:...",
            "packet_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-v955",
            "packet_status": "downstream_publication_receipt_packet_ready",
            "granted_use": "downstream_governance_lookup_only",
            "contract_check_ready": True,
            "promotion_ready": False,
        }
    ],
    "source_evidence_count": 2,
    "lookup_ready": True,
    "contract_check_ready": True,
    "next_step": "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index",
}
```

`packet_index_rows` 是给后续 review 消费的扁平索引。它只暴露 lookup-only 消费所需字段，同时保留 source packet 和 source packet check 路径。

## 核心检查逻辑

`_checks()` 生成 27 条检查：

- `receipt_packet_file_exists` 与 `receipt_packet_check_file_exists`：两个源文件必须存在。
- `receipt_packet_passed` 与 `receipt_packet_decision_ready`：v955 packet 必须 ready。
- `receipt_packet_summary_ready`：summary 与 packet body 必须 ready。
- `receipt_packet_check_passed`、`receipt_packet_check_decision_ready`、`contract_check_ready`：v956 check 必须通过。
- `packet_status_matches_check`：packet status 必须与 original/rebuilt check 一致。
- `granted_use_lookup_only`：packet 与 check 两侧都必须保持 lookup-only。
- `lookup_ready`、`packet_rows_present`、`source_evidence_rows_present`：lookup、packet row、source evidence row 必须齐全。
- `source_evidence_passed` 与 `source_evidence_files_exist`：两条 source evidence 必须通过且文件仍存在。
- `lookup_key_namespace`：lookup key 必须属于 `publication:`。
- `source_receipt_review_file_exists`、`source_publication_receipt_file_exists`、`source_index_review_file_exists`、`source_publication_file_exists`、`source_publication_check_file_exists`：上游 source artifacts 必须仍存在。
- `consumer_boundary_governance` 与 `model_quality_claim_bounded`：消费边界和模型声称必须保守。
- `promotion_still_false`：packet 与 check 都不能打开 promotion。
- `source_packet_checks_clean` 与 `source_contract_checks_clean`：v955/v956 检查必须 clean。
- `source_next_steps_match`：v955 路由到 check，v956 路由到 index。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index.py --receipt-packet e\955\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet --receipt-packet-check e\956\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check --out-dir e\957\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index --require-index-ready --require-lookup-ready --force
```

流程：

1. 定位 v955 packet JSON 和 v956 check JSON。
2. 读取 packet summary/body、packet rows、source evidence rows 和 check summary。
3. 校验 packet 与 check 的状态、用途、计数、source 文件和 no-promotion 字段。
4. 输出 index JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 5 个场景：

- ready packet + ready check 可以生成 index。
- contract check 失败时 index 失败。
- packet granted use 漂移到 production promotion 时失败。
- CLI 在 `--require-index-ready` 下对篡改 packet 返回 1。
- artifact writer 和 CLI 输出完整。

这组测试保护后续 review 不会绕过 contract check 直接消费 packet。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_ready
failed_count=0
packet_index_id=randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-v957
lookup_scope=downstream_governance_lookup_only
granted_use=downstream_governance_lookup_only
lookup_ready=True
contract_check_ready=True
packet_index_row_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=27
failed_check_count=0
```

Playwright MCP 截图：

```text
e/957/图片/v957-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index.png
```

## 一句话总结

v957 把通过 contract check 的 receipt packet 索引成 lookup-only 入口，给下一步 index review 准备了稳定输入。

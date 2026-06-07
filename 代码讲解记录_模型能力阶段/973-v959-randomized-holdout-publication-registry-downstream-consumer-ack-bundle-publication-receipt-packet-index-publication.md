# v959 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication

## 本版目标与边界

v959 的目标是把 v958 审查通过的 receipt packet index 发布为 lookup-only publication。v958 只是 review，v959 才形成供下一步 contract check 消费的 publication artifact。

这版不训练模型，不扩展质量声明，不批准 production promotion。它只把 v957 index 经 v958 review 后的结果发布成只读查找产物。

前置链路：

```text
v955 publication receipt packet
 -> v956 publication receipt packet contract check
 -> v957 publication receipt packet index
 -> v958 publication receipt packet index review
 -> v959 publication receipt packet index publication
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.py`
  - v959 核心 publication builder。
  - 读取 v958 review 的 summary 与 review body，检查 review ready、publish ready、lookup ready、source 文件、计数、用途和 no-promotion。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 Publication Boundary 和全部 checks。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.py`
  - v959 CLI。
  - 支持 `--require-publication-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.py`
  - 覆盖 ready publication、review 未 publish-ready、index 文件丢失、allowed use 漂移和 artifact/CLI 输出。

- `e/959/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication/`
  - 使用真实 v958 review 生成的运行证据。

## 核心数据结构

`publication` 是本版主结构：

```python
{
    "publication_ready": True,
    "publication_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-v959",
    "publication_status": "published_for_downstream_receipt_packet_index_lookup_only",
    "receipt_packet_index_review_path": "...v958...index_review.json",
    "receipt_packet_index_path": "...v957...index.json",
    "source_packet_path": "...v955...packet.json",
    "source_packet_check_path": "...v956...packet_check.json",
    "published_use": "downstream_governance_lookup_only",
    "packet_index_row_count": 1,
    "source_packet_row_count": 1,
    "source_evidence_count": 2,
    "promotion_ready": False,
    "next_step": "check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication",
}
```

这个结构把 review 的批准结果落到 publication 层，同时保留 source index、source packet 和 source packet check 路径，让下一步 contract check 能重新定位上游证据。

## 核心检查逻辑

`_checks()` 生成 21 条检查：

- `receipt_packet_index_review_file_exists`：v958 review 文件必须存在。
- `receipt_packet_index_review_passed` 与 `receipt_packet_index_review_decision_ready`：v958 review 必须通过且 decision ready。
- `receipt_packet_index_review_summary_ready`：summary 与 review body 的 ready 状态必须一致。
- `review_status_publishable`：review status 必须批准 receipt packet index publication。
- `receipt_packet_index_file_exists`、`source_packet_file_exists`、`source_packet_check_file_exists`：v957 index、v955 packet、v956 check 文件必须仍存在。
- `downstream_ready`、`publish_ready`、`lookup_ready`、`contract_check_ready`：review 必须具备发布所需信号。
- `packet_index_row_count`、`source_packet_row_count`、`source_evidence_count`：关键计数必须保持 1/1/2。
- `allowed_use_lookup_only`：用途必须保持 `downstream_governance_lookup_only`。
- `consumer_boundary_governance` 与 `model_quality_claim_bounded`：边界与模型声明必须保守。
- `promotion_still_false`：summary、review body 和 approved 字段都不能打开 promotion。
- `source_checks_clean`：v958 failed check count 必须为 0。
- `source_next_step_matches`：v958 必须路由到 publication。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.py e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review --out-dir e\959\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication --require-publication-ready --require-lookup-ready --force
```

流程：

1. 定位 v958 receipt packet index review JSON。
2. 读取 review summary 与 review body。
3. 校验 review status、source 文件、用途、计数、next step 和 no-promotion。
4. 输出 publication JSON、CSV、TXT、Markdown、HTML。
5. 如果 `--require-publication-ready` 或 `--require-lookup-ready` 不满足，CLI 返回 1。

## 测试覆盖

新增测试覆盖 5 个场景：

- ready v958 review 可以生成 publication。
- review 的 `publish_ready` 被篡改为 false 时失败。
- review 指向的 v957 index 文件缺失时失败。
- allowed use 漂移到 production promotion 时失败。
- artifact writer 和 CLI 输出完整。

这组测试保护的是发布层边界：publication 只能发布一个已经 review、仍可追溯、用途未漂移的 lookup-only packet index。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_ready
failed_count=0
publication_status=published_for_downstream_receipt_packet_index_lookup_only
published_use=downstream_governance_lookup_only
publish_ready=True
lookup_ready=True
contract_check_ready=True
packet_index_row_count=1
source_packet_row_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=21
failed_check_count=0
```

Playwright MCP 截图：

```text
e/959/图片/v959-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication.png
```

## 一句话总结

v959 将已审查的 receipt packet index 发布为 lookup-only 产物，同时继续保留 contract check 和 promotion 阻断边界。

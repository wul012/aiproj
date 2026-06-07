# v958 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index review

## 本版目标与边界

v958 的目标是审查 v957 生成的 receipt packet index，并确认它可以作为 lookup-only publication 的输入继续向后传递。

这版不训练模型，不比较 checkpoint，也不批准生产 promotion。它只回答一个工程治理问题：v957 packet index 是否仍然完整、保守、可追溯，并且是否只允许 downstream governance lookup。

前置链路：

```text
v955 publication receipt packet
 -> v956 publication receipt packet contract check
 -> v957 publication receipt packet index
 -> v958 publication receipt packet index review
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.py`
  - v958 核心 review builder。
  - 读取 v957 index 的 summary、packet_index、packet_index_rows、source_packet_rows 和 source_evidence_rows。
  - 产出 `review`、`summary`、`check_rows`、`issues` 和 `interpretation`。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 Review Boundary、source packet、source packet check、next step 和全部检查结果。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.py`
  - v958 CLI。
  - 支持输入 JSON 文件或输出目录，支持 `--require-review-ready`、`--require-downstream-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.py`
  - 覆盖 ready review、source evidence 丢失、lookup use 漂移、CLI 失败退出和 artifact 输出。

- `e/958/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review/`
  - 使用真实 v957 index 生成的运行证据。

## 核心数据结构

`review` 是本版的主结构：

```python
{
    "review_ready": True,
    "review_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review-v958",
    "review_status": "approved_for_downstream_receipt_packet_index_publication",
    "packet_index_row_count": 1,
    "source_packet_row_count": 1,
    "source_evidence_count": 2,
    "downstream_ready": True,
    "lookup_ready": True,
    "contract_check_ready": True,
    "publish_ready": True,
    "allowed_use": "downstream_governance_lookup_only",
    "promotion_ready": False,
    "next_step": "publish_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index",
}
```

这个结构的重点不是“模型更强”，而是“下游消费更稳”。它把 v957 index 的 source packet、source packet check 和 source evidence 重新确认一遍，避免后续 publication 消费一个已经漂移或缺源的索引。

## 核心检查逻辑

`_checks()` 生成 23 条检查：

- `receipt_packet_index_file_exists`：v957 index 文件必须存在。
- `receipt_packet_index_passed` 与 `receipt_packet_index_decision_ready`：v957 index 必须通过且 decision ready。
- `receipt_packet_index_summary_ready`：summary 与 body 中的 index ready 必须一致。
- `lookup_scope_downstream` 与 `granted_use_lookup_only`：lookup scope 和 granted use 必须保持 `downstream_governance_lookup_only`。
- `lookup_ready` 与 `contract_check_ready`：v957 index 必须已经包含 lookup 和 contract check 信号。
- `packet_index_rows_present`：必须只有一条 packet index row。
- `source_packet_rows_present`：必须保留一条 source packet row，证明 index 仍可追溯到 packet 层。
- `lookup_keys_present`：lookup key 必须属于 `publication:` namespace。
- `packet_index_rows_not_promoted` 与 `source_packet_rows_not_promoted`：index row 与 source packet row 都不能打开 promotion。
- `source_evidence_count`、`source_evidence_passed`、`source_evidence_files_exist`：两条 source evidence 必须存在且通过。
- `source_packet_file_exists` 与 `source_packet_check_file_exists`：v955 packet 与 v956 check 文件必须仍存在。
- `consumer_boundary_governance` 与 `model_quality_claim_bounded`：边界和模型声明必须保持保守。
- `promotion_still_false`：summary、body、approved 字段都不能批准 promotion。
- `source_checks_clean`：v957 index 的 failed check count 必须为 0。
- `source_next_step_matches`：v957 必须路由到 v958 review。

## CLI 运行流程

真实命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review.py e\957\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index --out-dir e\958\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review --require-review-ready --require-downstream-ready --force
```

流程：

1. 定位 v957 receipt packet index JSON。
2. 读取 index summary、packet_index、packet_index_rows、source_packet_rows 和 source_evidence_rows。
3. 校验 ready 状态、lookup-only 用途、source 文件、source evidence、next step 和 no-promotion 字段。
4. 输出 review JSON、CSV、TXT、Markdown、HTML。
5. 如果 `--require-review-ready` 或 `--require-downstream-ready` 不满足，CLI 返回 1。

## 测试覆盖

新增测试覆盖 5 个场景：

- ready v957 index 可以生成 review。
- source evidence 路径被篡改时 review 失败。
- granted use 漂移到 production promotion 时 review 失败。
- CLI 在 `--require-review-ready` 下对篡改 index 返回 1。
- artifact writer 和 CLI 输出完整。

这组测试保护的是 publication 前的输入完整性：后续步骤不能绕过 index review 直接发布一个缺 source 或用途漂移的 packet index。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_review_ready
failed_count=0
review_status=approved_for_downstream_receipt_packet_index_publication
packet_index_row_count=1
source_packet_row_count=1
source_evidence_count=2
downstream_ready=True
lookup_ready=True
contract_check_ready=True
publish_ready=True
allowed_use=downstream_governance_lookup_only
promotion_ready=False
passed_check_count=23
failed_check_count=0
```

Playwright MCP 截图：

```text
e/958/图片/v958-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-review.png
```

## 一句话总结

v958 把 v957 packet index 审查为 lookup-only publication 的合格输入，同时继续阻断生产 promotion 和更强模型质量声明。

# v969 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication

## 本版目标与边界

v969 的目标是把 v968 review 发布成 lookup-only publication。v968 已确认 v967 receipt packet index 可以进入 publication，v969 负责生成 publication 产物，并把下一步路由到 contract check。

这版不训练模型，不扩大模型质量声明，不批准 production promotion。publication 只表示下游可以治理查询。

前置链路：

```text
v967 receipt packet index
 -> v968 receipt packet index review
 -> v969 receipt packet index publication
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.py`
  - v969 核心 publication builder。
  - 读取 v968 review，检查 review status、publish_ready、lookup_ready、contract_check_ready、source paths 和 no-promotion。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 publication boundary 和 checks。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.py`
  - v969 CLI。
  - 支持 `--require-publication-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.py`
  - 覆盖 ready publication、publish_ready 漂移、index file 缺失、allowed use 漂移和 CLI/artifact 输出。

- `e/969/解释/publication-receipt-packet-index-publication/`
  - 使用真实 v968 review 生成的运行证据。

## 核心数据结构

`publication` 是主结构：

```python
{
    "publication_ready": True,
    "publication_id": "...v969",
    "publication_status": "published_for_downstream_receipt_packet_index_publication_receipt_packet_index_lookup_only",
    "receipt_packet_index_review_path": "...v968 json...",
    "receipt_packet_index_path": "...v967 json...",
    "published_use": "downstream_governance_lookup_only",
    "publish_ready": True,
    "lookup_ready": True,
    "contract_check_ready": True,
    "receipt_packet_index_row_count": 1,
    "source_packet_row_count": 1,
    "source_evidence_count": 2,
    "promotion_ready": False,
    "next_step": "check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication",
}
```

## 21 项检查

`_checks()` 保护以下边界：

- v968 review 文件存在，status/decision ready。
- summary 和 body 都 review ready。
- review status 必须批准 lookup-only publication。
- v967 index、source packet、source packet check 文件仍存在。
- downstream_ready、publish_ready、lookup_ready、contract_check_ready 都为 true。
- receipt packet index row 为 1 条。
- source packet row 为 1 条。
- source evidence count 为 2。
- allowed use 仍是 downstream governance lookup only。
- consumer boundary 与 model quality claim 保守。
- promotion_ready 和 approved_for_promotion 都为 false。
- v968 failed_check_count 为 0。
- v968 next step 必须指向 v969 publication。

## 测试覆盖

聚焦测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.py -q -o cache_dir=runs\pytest-cache-v969-focus
```

结果：

```text
10 passed
```

全量验证：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v969-full
```

结果：

```text
2214 passed
```

Source encoding hygiene：

```text
status=pass, source_count=1738, syntax_error_count=0
```

## 运行证据

真实 v969 evidence 来自 v968：

```text
status=pass
failed_count=0
publication_status=published_for_downstream_receipt_packet_index_publication_receipt_packet_index_lookup_only
published_use=downstream_governance_lookup_only
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=21
failed_check_count=0
```

Playwright MCP 打开 HTML 报告并保存：

- `e/969/解释/v969-playwright-snapshot.md`
- `e/969/图片/v969-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication.png`

## 一句话总结

v969 把 v968 review 转成 lookup-only publication，并把下一步严格路由到 contract check。

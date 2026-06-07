# v965 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet

## 本版目标与边界

v965 的目标是把 v964 review 转成 receipt packet。v964 证明 v963 receipt 可以进入 packet construction，v965 真正生成 packet rows 和 source evidence rows，让下一步 contract check 有稳定输入。

这版不训练模型，不生成新的模型质量声明，不批准 production promotion。

前置链路：

```text
v963 receipt packet index publication receipt
 -> v964 receipt packet index publication receipt review
 -> v965 receipt packet index publication receipt packet
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.py`
  - v965 核心 packet builder。
  - 读取 v964 review，校验 packet-ready、lookup-only、source artifact、digest shape 和 no-promotion。
  - 输出 `packet`、`packet_rows`、`source_evidence_rows`。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 写 packet row；HTML 展示 packet boundary、digest、packet rows 和 checks。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.py`
  - v965 CLI。
  - 支持 `--receipt-review`、`--require-packet-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.py`
  - 覆盖 ready packet、granted use 漂移、lookup-key namespace 漂移、source publication 缺失和 CLI/artifact 输出。

- `e/965/解释/publication-receipt-packet/`
  - 使用真实 v964 review 生成的运行证据。

## 核心数据结构

`packet` 是本版主结构：

```python
{
    "packet_ready": True,
    "packet_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-v965",
    "packet_status": "downstream_receipt_packet_index_publication_receipt_packet_ready",
    "receipt_review_sha256": "...64 hex chars...",
    "publication_receipt_sha256": "...64 hex chars...",
    "granted_use": "downstream_governance_lookup_only",
    "publication_index_row_count": 1,
    "source_evidence_count": 2,
    "consumer_receipt_count": 1,
    "promotion_ready": False,
    "next_step": "check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet",
}
```

`source_evidence_rows` 固定两条：

- `receipt_review`：v964 review 文件与 SHA-256。
- `publication_receipt`：v963 receipt 文件与 SHA-256。

`packet_rows` 则把 consumer、lookup key、publication id、granted use 和 packet status 放到一行中，供下一版 check 逐字段验证。

## 28 项检查

`_checks()` 保护以下边界：

- v964 review 文件存在且 status/decision ready。
- summary/body review ready 与 packet ready 都成立。
- receipt status 保持 lookup receipted。
- granted use 仍为 downstream governance lookup only。
- blocked uses 完整。
- publication index row 与 consumer receipt row 都刚好 1 条。
- lookup key 仍是 `publication:` namespace。
- consumer rows 和 publication rows 都不能 promotion。
- receipt review digest 与 publication receipt digest 都必须是 sha256 形状。
- source index review、source publication、source publication check、source review、source index 必须存在。
- promotion 与 approved_for_promotion 都必须 false。
- consumer boundary 与 model quality claim 保持保守。
- v964 failed checks 必须为 0。
- v964 next step 必须指向 v965 packet。

这些检查保证 packet 是从 v964 review 合法构建出来的，而不是绕过 receipt review 直接拼文件。

## 测试覆盖

聚焦测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet.py -q -o cache_dir=runs\pytest-cache-v965-focus
```

结果：

```text
10 passed
```

全量验证：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v965-full
```

结果：

```text
2193 passed
```

## 运行证据

真实 v965 evidence 来自 v964：

```text
status=pass
failed_count=0
packet_status=downstream_receipt_packet_index_publication_receipt_packet_ready
lookup_ready=True
source_evidence_count=2
consumer_receipt_count=1
promotion_ready=False
passed_check_count=28
failed_check_count=0
```

Playwright MCP 打开 HTML 报告并保存：

- `e/965/解释/v965-playwright-snapshot.md`
- `e/965/图片/v965-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet.png`

## 一句话总结

v965 把 v964 的 receipt review 转成可 contract check 的 receipt packet，并继续保持 lookup-only 与 no-promotion。

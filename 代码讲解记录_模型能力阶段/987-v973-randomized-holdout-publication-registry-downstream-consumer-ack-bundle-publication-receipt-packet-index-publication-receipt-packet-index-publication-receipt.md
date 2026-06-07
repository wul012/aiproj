# v973 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication receipt

## 本版目标与边界

v973 的目标是把 v972 publication index review 记录成 downstream consumer receipt。v972 审核了 v971 index，确认它可以进入 receipt 记录；v973 则把这次授权落成一份可复核收据。

本版不训练模型，不改变 checkpoint，不扩大模型质量声明，不批准 production promotion。它只授予 `downstream_governance_lookup_only`，并保留 blocked uses。

前置链路：

```text
v971 publication index
 -> v972 publication index review
 -> v973 downstream consumer receipt
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.py`
  - v973 核心 receipt builder。
  - 读取 v972 review，检查 receipt_ready、lookup-only request、blocked uses、source paths、digest 和 no-promotion。
- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 输出 consumer receipt 行，HTML 展示 receipt boundary、digest 和 checks。
- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.py`
  - v973 CLI。
  - 支持 `--index-review`、`--consumer-name`、`--requested-use`、`--require-receipt-ready`、`--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.py`
  - 覆盖 ready receipt、promotion request 拒绝、source review 缺失、CLI/artifact 输出。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v973 下一步：`review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt`。
- `src/minigpt/__init__.py`
  - 接入 v973 build/write lazy export。

## 核心数据结构

`receipt` 是本版主结构：

```python
{
    "receipt_ready": True,
    "receipt_id": "...receipt-v973",
    "receipt_type": "...receipt_packet_index_publication_receipt_packet_index_publication",
    "receipt_status": "downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "requested_use": "downstream_governance_lookup_only",
    "granted_use": "downstream_governance_lookup_only",
    "index_review_path": "...v972 json...",
    "index_review_sha256": "<64 hex chars>",
    "publication_index_row_count": 1,
    "lookup_keys": ["publication:<publication_id>"],
    "blocked_uses": [
        "production_promotion",
        "model_quality_expansion",
        "training_data_claim_expansion",
    ],
    "promotion_ready": False,
    "next_step": "review_...",
}
```

`index_review_sha256` 是 v973 的关键证据字段。它让 receipt 可以绑定 v972 review 文件，而不是只保存路径字符串。

## 23 项检查保护什么

`_checks()` 覆盖：

- v972 review 文件存在。
- review status 和 decision ready。
- summary/body 都 ready。
- review status 允许 receipt recording。
- requested use 必须是 downstream governance lookup only。
- blocked uses 必须完整。
- downstream_ready、lookup_ready、contract_check_ready、receipt_ready 全部为 true。
- publication index row 恰好 1 行。
- lookup key 使用 publication namespace。
- index row 不能 promotion。
- source publication、source publication check、source review、source index 文件都存在。
- consumer boundary 和 model quality claim 保守。
- promotion_ready 和 approved_for_promotion 都为 false。
- source failed_check_count 为 0。
- v972 next step 必须指向 v973 receipt。

这些检查把 receipt 限定为“治理消费者收据”，而不是“业务发布许可”。

## 测试覆盖

焦点测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_review.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.py -q -o cache_dir=runs\pytest-cache-v973-focus
```

结果：

```text
9 passed
```

关键断言：

- ready v972 review 可以生成 receipt。
- `requested_use=production_promotion` 会失败。
- source review 缺失会失败。
- receipt digest 是 64 位 SHA-256。
- JSON/CSV/TXT/Markdown/HTML 输出可用。

全量测试：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v973-full
```

结果：

```text
2232 passed
```

Source encoding hygiene：

```text
status=pass, source_count=1754, bom_count=0, syntax_error_count=0
```

## 运行证据

真实 evidence 命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.py --index-review e\972\解释\publication-receipt-packet-index-publication-index-review --out-dir e\973\解释\publication-receipt-packet-index-publication-receipt --require-receipt-ready --force
```

关键输出：

```text
status=pass
receipt_status=downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted
granted_use=downstream_governance_lookup_only
publication_index_row_count=1
lookup_key_count=1
promotion_ready=False
passed_check_count=23
failed_check_count=0
```

Playwright MCP 截图和快照：

- `e/973/图片/v973-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt.png`
- `e/973/解释/v973-playwright-snapshot.md`

## 一句话总结

v973 把 v972 review 转成带 digest 的 lookup-only consumer receipt，为后续 receipt review 提供稳定证据入口。

# v963 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt

## 本版目标与边界

v963 的目标是消费 v962 的 publication index review，并记录一条 lookup-only receipt。v962 证明 v961 index 可以进入 receipt recording；v963 则把这个接收动作落成 JSON/CSV/HTML 证据。

这版不训练模型，不生成新质量声明，不批准 promotion。它只是记录下游治理 reader 已接收 v962 review，并把 granted use 限定为 `downstream_governance_lookup_only`。

前置链路：

```text
v961 receipt packet index publication index
 -> v962 receipt packet index publication index review
 -> v963 receipt packet index publication receipt
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.py`
  - v963 核心 receipt builder。
  - 读取 v962 review，校验 review ready、receipt ready、lookup-only、source artifact、blocked uses 和 no-promotion。
  - 记录 v962 review 文件的 SHA-256。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 写 consumer receipt row；HTML 展示 receipt boundary、digest、consumer receipt 和 checks。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.py`
  - v963 CLI。
  - 支持 `--index-review`、`--consumer-name`、`--requested-use`、`--require-receipt-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.py`
  - 覆盖 ready receipt、promotion request 拒绝、source review 缺失、artifact/CLI 输出。

- `e/963/解释/publication-index-receipt/`
  - 使用真实 v962 review 生成的 v963 运行证据。

## 核心数据结构

v963 的核心输出是 `receipt`：

```python
{
    "receipt_ready": True,
    "receipt_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-v963",
    "receipt_status": "downstream_receipt_packet_index_publication_lookup_receipted",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "granted_use": "downstream_governance_lookup_only",
    "index_review_sha256": "...64 hex chars...",
    "publication_index_row_count": 1,
    "lookup_keys": ["publication:..."],
    "blocked_uses": ["production_promotion", "model_quality_expansion", "training_data_claim_expansion"],
    "promotion_ready": False,
    "next_step": "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt",
}
```

`consumer_receipts` 是面向下游消费者的行级记录：

```python
{
    "consumer_name": "publication_registry_governance_lookup_reader",
    "lookup_key": "publication:...",
    "publication_id": "...",
    "granted_use": "downstream_governance_lookup_only",
    "promotion_ready": False,
    "receipt_status": "downstream_receipt_packet_index_publication_lookup_receipted",
}
```

这两个结构共同表达：下游 reader 已接收 v962 review，但只能做治理查询，不能拿它当生产晋升证据。

## 核心检查逻辑

`_checks()` 生成 23 条检查：

- v962 review 文件必须存在。
- review 顶层 status 必须是 `pass`。
- review decision 必须是 v962 ready decision。
- summary ready 与 body `review_ready` 必须同时为 true。
- review status 必须是 `approved_for_downstream_receipt_packet_index_publication_receipt`。
- requested use 必须是 downstream governance lookup only。
- blocked uses 必须包含 production promotion、model quality expansion、training data claim expansion。
- downstream、lookup、contract check、receipt ready 必须都成立。
- publication index row 必须刚好 1 条。
- lookup key 必须使用 `publication:` namespace。
- publication index row 不能 promotion。
- source publication、source publication check、source review、source index 必须仍然存在。
- consumer boundary 与 model quality claim 必须保持保守。
- summary/body/approved 都不能开启 promotion。
- v962 failed check count 必须为 0。
- v962 next step 必须指向 v963 receipt。

这批检查让 receipt 不只是“写一条记录”，而是确认接收动作仍然绑定到完整上游证据链。

## CLI 与退出码

真实运行命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.py --index-review e\962\解释\receipt-packet-index-publication-index-review --out-dir e\963\解释\publication-index-receipt --require-receipt-ready --force
```

`--require-receipt-ready` 会在 receipt 不可记录时返回 1。`--require-promotion-ready` 仍会返回 1，因为这条链路明确不批准 promotion。

## 测试覆盖

聚焦测试覆盖：

- ready v962 review 可以生成 `status=pass`、receipt ready、digest、lookup-only granted use。
- 请求 `production_promotion` 会触发 `requested_use_allowed` failure。
- source review 被改成不存在路径时，会触发 `source_review_file_exists` failure。
- CLI 可从目录定位 review JSON 并写出五类 artifact。

聚焦测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.py -q -o cache_dir=runs\pytest-cache-v963-focus
```

结果：

```text
9 passed
```

全量验证：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v963-full
```

结果：

```text
2183 passed
```

## 运行证据

v963 使用真实 v962 review 生成：

```text
status=pass
failed_count=0
receipt_status=downstream_receipt_packet_index_publication_lookup_receipted
granted_use=downstream_governance_lookup_only
publication_index_row_count=1
lookup_key_count=1
promotion_ready=False
passed_check_count=23
failed_check_count=0
```

Playwright MCP 打开 HTML 报告并保存：

- `e/963/解释/v963-playwright-snapshot.md`
- `e/963/图片/v963-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt.png`

## 一句话总结

v963 把 v962 的可接收 review 变成 digest-backed lookup-only receipt，让下游消费动作本身也进入可审计证据链。

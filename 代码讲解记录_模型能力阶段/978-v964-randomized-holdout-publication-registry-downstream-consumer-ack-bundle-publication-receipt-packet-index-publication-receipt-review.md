# v964 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt review

## 本版目标与边界

v964 的目标是 review v963 的 lookup-only receipt，并判断它能否进入 receipt-packet construction。v963 已经记录了 downstream receipt 和 v962 review digest，v964 再检查这条 receipt 是否仍然可信、可追溯、未越权。

这版不训练模型，不生成新的模型质量结论，不批准 production promotion。

前置链路：

```text
v962 receipt packet index publication index review
 -> v963 receipt packet index publication receipt
 -> v964 receipt packet index publication receipt review
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review.py`
  - v964 核心 review builder。
  - 读取 v963 receipt，校验 receipt ready、granted use、consumer receipt、source digest、source 文件与 no-promotion。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 review boundary、receipt SHA-256、consumer receipts 和所有 checks。

- `scripts/review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.py`
  - v964 CLI。
  - 支持 `--receipt`、`--require-review-ready`、`--require-packet-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review.py`
  - 覆盖 ready receipt review、granted use 漂移、digest 漂移、source index review 缺失和 CLI/artifact 输出。

- `e/964/解释/publication-receipt-review/`
  - 使用真实 v963 receipt 生成的运行证据。

## 核心数据结构

`review` 是本版的主结构：

```python
{
    "review_ready": True,
    "review_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-review-v964",
    "review_status": "approved_for_downstream_receipt_packet_index_publication_receipt_packet",
    "publication_receipt_sha256": "...64 hex chars...",
    "packet_ready": True,
    "receipt_status": "downstream_receipt_packet_index_publication_lookup_receipted",
    "granted_use": "downstream_governance_lookup_only",
    "publication_index_row_count": 1,
    "consumer_receipt_count": 1,
    "promotion_ready": False,
    "next_step": "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet",
}
```

`publication_receipt_sha256` 是 v963 receipt 文件本身的 digest，`index_review_sha256` 仍然来自 v963 并被重新验证。这样 v964 同时证明“审的是哪份 receipt”和“receipt 绑定的 v962 review 没漂移”。

## 25 项检查

`_checks()` 保护以下边界：

- v963 receipt 文件必须存在。
- receipt 顶层 status 必须是 `pass`。
- decision 必须是 v963 ready decision。
- summary ready 与 body `receipt_ready` 必须同时为 true。
- receipt status 必须是 downstream lookup receipted。
- granted use 必须保持 downstream governance lookup only。
- blocked uses 必须完整。
- publication index row 与 consumer receipt row 都必须刚好 1 条。
- lookup key 必须保持 `publication:` namespace。
- consumer receipt row 只能 lookup-only。
- publication index row 与 consumer receipt row 都不能 promotion。
- summary/body/approved 都不能开启 promotion。
- consumer boundary 与 model quality claim 必须保守。
- source index review、source publication、source publication check、source review、source index 文件必须存在。
- v963 记录的 v962 review digest 必须是 64 位小写 sha256，并且必须与源文件实际 digest 匹配。
- v963 failed check count 必须为 0。
- v963 next step 必须指向 v964 review。

这些检查让 receipt-packet construction 只接受 digest-backed receipt，而不是任意 receipt 文件。

## CLI 与退出码

真实运行命令：

```powershell
python scripts\review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.py --receipt e\963\解释\publication-index-receipt --out-dir e\964\解释\publication-receipt-review --require-review-ready --require-packet-ready --force
```

`--require-review-ready` 与 `--require-packet-ready` 都通过时返回 0。`--require-promotion-ready` 仍会返回 1，因为 promotion 不在本链路允许范围内。

## 测试覆盖

聚焦测试覆盖：

- ready receipt 可以生成 `status=pass`、review ready、packet ready。
- `granted_use` 被改成 `production_promotion` 会失败。
- `index_review_sha256` 被篡改会失败。
- source index review 路径缺失会失败。
- CLI 能从 receipt 输出目录定位 JSON 并写出五类 artifact。

聚焦测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_review.py -q -o cache_dir=runs\pytest-cache-v964-focus
```

结果：

```text
9 passed
```

全量验证：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v964-full
```

结果：

```text
2188 passed
```

## 运行证据

真实 v964 evidence 来自 v963：

```text
status=pass
failed_count=0
review_status=approved_for_downstream_receipt_packet_index_publication_receipt_packet
packet_ready=True
granted_use=downstream_governance_lookup_only
publication_index_row_count=1
consumer_receipt_count=1
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

Playwright MCP 打开 HTML 报告并保存：

- `e/964/解释/v964-playwright-snapshot.md`
- `e/964/图片/v964-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-review.png`

## 一句话总结

v964 把 v963 的 digest-backed receipt 推进到可构建 receipt packet 的状态，同时继续把 production promotion 留在阻断区。

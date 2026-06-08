# v974 randomized holdout publication receipt packet index publication receipt review 代码讲解

## 本版目标和边界

v974 接在 v973 后面。v973 已经从 v972 的 index review 记录了一份 downstream consumer receipt，说明某个 governance lookup reader 可以读取这条 randomized holdout publication registry 证据，但用途只限 downstream governance lookup。

本版新增的是 receipt review：它重新检查 v973 receipt 是否仍然满足只读、lookup-only、digest-backed、no-promotion 的边界，然后才允许进入下一步 receipt packet construction。

本版明确不做三件事：

- 不训练模型。
- 不扩大 `bounded_randomized_target_hidden_holdout_claim_only` 之外的模型质量声明。
- 不把 receipt review 变成 production promotion 或 training data claim expansion。

## 前置链路

本版依赖的直接输入是 v973 的正式归档：

```text
e/973/解释/publication-receipt-packet-index-publication-receipt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.json
```

v973 的 receipt 已经保留：

- `receipt_status=downstream_receipt_packet_index_publication_receipt_packet_index_publication_lookup_receipted`
- `granted_use=downstream_governance_lookup_only`
- 一条 publication index row
- 一条 consumer receipt row
- `index_review_path` 和 `index_review_sha256`
- `source_publication_path`
- `source_publication_check_path`
- `source_review_path`
- `source_index_path`
- `next_step=review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt`

v974 的任务是证明这些字段仍然一致、可读、可复核。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.py`

这是本版核心 builder。它提供：

- `locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt`
- `read_json_report`
- `build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review`
- `resolve_exit_code`

`build_*_review()` 的输入是 v973 receipt JSON 反序列化后的 dict，输出是一份新的 review report。输出结构包括：

- `status`
- `decision`
- `failed_count`
- `issues`
- `publication_receipt_path`
- `publication_receipt_sha256`
- `source_publication_receipt_summary`
- `source_publication_receipt`
- `publication_index_rows`
- `consumer_receipts`
- `check_rows`
- `review`
- `summary`
- `interpretation`

这里最重要的是 `check_rows` 和 `summary`。`check_rows` 是逐项证据，`summary` 是后续模块可以消费的稳定摘要。

### `_checks()`

`_checks()` 是防漂移的核心。它保护 25 个条件：

- v973 receipt 文件必须存在。
- v973 receipt 自身必须 `status=pass`。
- v973 decision 必须是 receipt ready。
- summary 和 receipt body 都必须 ready。
- receipt status 必须仍然是 lookup receipted。
- granted use 必须仍然是 `downstream_governance_lookup_only`。
- blocked uses 必须完整包含 production promotion、model quality expansion、training data claim expansion。
- publication index rows 和 consumer receipts 都必须各为 1。
- lookup key 必须仍然属于 `publication:` namespace。
- publication index rows 和 consumer receipt rows 都不能被 promotion。
- summary、receipt、approved flag 都必须保持 no-promotion。
- consumer boundary 必须仍然是 governance lookup only。
- model quality claim 必须仍然是 bounded randomized holdout claim。
- 源 index review、source publication、source publication check、source review、source index 文件必须存在。
- `index_review_sha256` 必须是 64 位 lowercase sha256。
- `index_review_sha256` 必须与实际 `index_review_path` 文件内容重新计算的 digest 一致。
- 源 receipt failed check count 必须为 0。
- 源 receipt next step 必须指向本版 review。

这组检查的价值是把 handoff/receipt artifact 从“文本上存在”变成“能沿源证据重新复核”。

### `_review()` 和 `_summary()`

`_review()` 只在全部检查通过时生成可消费 review：

```text
review_ready=True
review_id=randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-review-v974
review_status=approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet
packet_ready=True
promotion_ready=False
approved_for_promotion=False
next_step=build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet
```

`_summary()` 把这些字段压缩成后续版本最容易消费的一层。后续 v975 如果构建 receipt packet，不需要重新理解整份 review，只要检查 summary 和必要源路径即可。

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_artifacts.py`

这个文件负责把 review report 写成 JSON、CSV、text、Markdown、HTML。

这里的 JSON 是最终机器证据；CSV 用于快速查看 consumer receipt row；text 用于 CLI 和 CI 摘要；Markdown/HTML 用于人工审阅和截图。

HTML 页面包含三块：

- Review Boundary：展示 review status、blocked uses、receipt sha256、source index review、next step。
- Consumer Receipts：展示 consumer、lookup key、publication id、granted use、blocked uses、promotion、status。
- Checks：逐项展示 25 个检查的 pass/fail、actual 和 detail。

### `scripts/review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.py`

这是命令行入口。它接收：

```powershell
--receipt <v973 receipt JSON 或输出目录>
--out-dir <v974 输出目录>
--require-review-ready
--require-packet-ready
--require-promotion-ready
--force
```

本版正式运行使用了 `--require-review-ready` 和 `--require-packet-ready`，没有使用 `--require-promotion-ready`，因为 promotion 在这条链上仍然必须保持 false。

### `src/minigpt/randomized_holdout_publication_constants.py`

本版新增：

```python
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_REVIEW_NEXT_STEP = "build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet"
```

这个常量让 v974 的 `next_step` 不再是散落字符串，而是进入统一路线表。后续如果 v975 构建 receipt packet，就能沿这个常量继续。

### `src/minigpt/__init__.py`

本版把 builder 和 output writer 加入 lazy export：

- `build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review`
- `write_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review_outputs`

这保持了仓库已有的包级导入习惯。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.py
```

测试覆盖四类行为：

- ready receipt 可以通过 review，并生成 `packet_ready=True`。
- 如果 granted use 被篡改成 `production_promotion`，review 必须失败。
- 如果源 index review digest 被篡改，review 必须失败。
- 如果源 index review path 缺失，review 必须失败。
- artifact writer 和 CLI 都能输出 JSON/CSV/text/Markdown/HTML。

这不是只测函数返回值，而是测了 source receipt -> review builder -> artifact writer -> CLI 的完整小闭环。

已运行聚焦测试：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.py -q -o cache_dir=runs\pytest-cache-v974-focus
```

结果：

```text
9 passed
```

## 运行证据

正式命令：

```powershell
python scripts\review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt.py --receipt e\973\解释\publication-receipt-packet-index-publication-receipt --out-dir e\974\解释\publication-receipt-packet-index-publication-receipt-review --require-review-ready --require-packet-ready --force
```

正式摘要：

```text
status=pass
failed_count=0
review_status=approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet
packet_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

截图归档：

```text
e/974/图片/v974-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-review.png
```

解释归档：

```text
e/974/解释/说明.md
```

## 一句话总结

v974 把 v973 的 lookup-only receipt 加上了 digest-backed review 保护，允许进入 receipt packet 构建，但仍然不允许生产晋升、模型质量扩张或训练数据声明扩张。

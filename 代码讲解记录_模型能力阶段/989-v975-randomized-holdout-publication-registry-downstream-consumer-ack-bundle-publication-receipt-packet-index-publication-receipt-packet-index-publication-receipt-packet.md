# v975 randomized holdout publication receipt packet 代码讲解

## 本版目标和边界

v975 接在 v974 receipt review 后面。v974 已经证明 v973 receipt 仍然是 lookup-only、digest-backed、no-promotion 的可复核交接产物。本版进一步把这份 review 打成 receipt packet，让后续 contract check 可以用一份更稳定的 packet report 来校验字段一致性。

本版不训练模型，不比较 checkpoint，不扩大模型质量声明，也不新增 production promotion 入口。它只做证据打包和边界保持。

## 前置链路

直接输入是 v974 正式 review：

```text
e/974/解释/publication-receipt-packet-index-publication-receipt-review/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.json
```

v974 review 已经确认：

- `review_ready=True`
- `packet_ready=True`
- `review_status=approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet`
- `granted_use=downstream_governance_lookup_only`
- `publication_index_row_count=1`
- `consumer_receipt_count=1`
- `promotion_ready=False`
- `failed_check_count=0`

v975 的责任是把这份 review 和它引用的 v973 receipt 固化为 packet evidence。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.py`

这是本版核心 builder。它提供：

- `locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review`
- `read_json_report`
- `build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet`
- `resolve_exit_code`

`build_*_packet()` 的输出包括：

- `receipt_review_path`
- `receipt_review_sha256`
- `source_receipt_review_summary`
- `source_receipt_review`
- `consumer_receipts`
- `publication_index_rows`
- `source_evidence_rows`
- `packet_rows`
- `check_rows`
- `packet`
- `summary`

其中 `source_evidence_rows` 是本版新产物的重点。它固定两条来源：

```text
receipt_review -> v974 review JSON
publication_receipt -> v973 receipt JSON
```

这让后续 contract check 可以同时看到“谁审过”和“审的是哪份原始 receipt”。

### `_checks()`

`_checks()` 包含 28 项检查。它保护的不是模型能力，而是治理证据是否还能被安全消费：

- v974 receipt review 文件存在。
- v974 receipt review 自身 `status=pass`。
- v974 decision 是 review ready。
- summary 和 review body 都 ready。
- review status 批准 receipt packet construction。
- `packet_ready=True`。
- receipt status 仍是 downstream lookup receipted。
- granted use 仍是 downstream governance lookup only。
- blocked uses 完整。
- publication index row 和 consumer receipt row 都为 1。
- lookup key 仍然是 `publication:` namespace。
- consumer receipt 和 publication row 都没有 promotion。
- receipt review sha256 和 publication receipt sha256 形状正确。
- source index review、source publication、source publication check、source review、source index 仍存在。
- `promotion_ready=False` 和 `approved_for_promotion=False`。
- consumer boundary 仍是 governance lookup only。
- model quality claim 仍是 bounded randomized target hidden holdout claim only。
- source failed checks 为 0。
- source next step 指向本版 packet builder。

这些检查保证 packet 不是随便复制 review 字段，而是重新验证了 source review 的可消费边界。

### `_packet()`

`_packet()` 在所有 checks 通过时生成 packet body：

```text
packet_ready=True
packet_id=randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-v975
packet_status=downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_ready
receipt_review_sha256=<v974 review digest>
publication_receipt_sha256=<v973 receipt digest>
source_evidence_count=2
granted_use=downstream_governance_lookup_only
promotion_ready=False
next_step=check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet
```

### `_packet_rows()`

`_packet_rows()` 把 consumer receipt 行映射成 packet row。它保留：

- packet id
- consumer name
- lookup key
- publication id
- granted use
- blocked uses
- promotion state
- receipt status
- packet status

这让 HTML/CSV 能直接展示 packet 的消费对象和用途。

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_artifacts.py`

artifact writer 输出 JSON、CSV、text、Markdown、HTML。

- JSON 是机器消费证据。
- CSV 用于快速看 packet row。
- text 是 CLI 摘要。
- Markdown 和 HTML 是人工审阅证据。

HTML 展示三块：

- Packet Boundary：digest、source index review、blocked uses、next step。
- Packet Rows：consumer、lookup key、publication、granted use、receipt status、packet status。
- Checks：28 个检查项。

### `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.py`

这是 CLI 入口。它支持：

```powershell
--receipt-review
--out-dir
--require-packet-ready
--require-lookup-ready
--require-promotion-ready
--force
```

这里有一个维护决策：没有加入 `--check-out-dir`。旧 v965 的脚本现在有 sidecar check 能力，但 v975 对应的 check 模块应由下一版 v976 提供。本版如果提前 import 一个不存在的 check 模块，会造成编译和 CI 风险，所以保持 packet builder 单一职责。

### `src/minigpt/randomized_holdout_publication_constants.py`

本版新增：

```python
RANDOMIZED_HOLDOUT_PUBLICATION_REGISTRY_DOWNSTREAM_CONSUMER_ACK_BUNDLE_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_RECEIPT_PACKET_NEXT_STEP = "check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet"
```

它把 v975 的下一步固定到常量表，避免后续链路靠散落字符串推进。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.py
```

测试覆盖：

- ready review 可以生成 packet。
- review granted use 被篡改为 production promotion 时必须失败。
- lookup key namespace 从 `publication:` 漂到 `model:` 时必须失败。
- source publication path 缺失时必须失败。
- artifact writer 和 CLI 输出 JSON/CSV/text/Markdown/HTML。

已运行聚焦测试：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_review.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.py -q -o cache_dir=runs\pytest-cache-v975-focus
```

结果：

```text
10 passed
```

## 运行证据

正式命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.py --receipt-review e\974\解释\publication-receipt-packet-index-publication-receipt-review --out-dir e\975\解释\publication-receipt-packet-index-publication-receipt-packet --require-packet-ready --require-lookup-ready --force
```

正式摘要：

```text
status=pass
packet_status=downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_ready
lookup_ready=True
source_evidence_count=2
promotion_ready=False
passed_check_count=28
failed_check_count=0
```

截图归档：

```text
e/975/图片/v975-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet.png
```

## 一句话总结

v975 把 v974 receipt review 和 v973 receipt 封装成 digest-backed packet，为下一版 contract check 提供稳定输入，同时继续把生产晋升和模型质量扩张挡在链外。

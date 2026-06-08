# v976 randomized holdout publication receipt packet contract check 代码讲解

## 本版目标和边界

v976 接在 v975 receipt packet 后面。v975 已经把 v974 receipt review 和 v973 receipt 打包成 digest-backed packet。本版新增 contract check：读取 v975 packet，回到它记录的 v974 review，再重新构建一份 packet，并把原始 packet 与 rebuilt packet 做字段级比对。

本版不新增治理链，不训练模型，不调整模型质量结论，也不允许 promotion。它是 v975 packet 的可重建性检查。

## 输入和输出

输入：

```text
e/975/解释/publication-receipt-packet-index-publication-receipt-packet/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.json
```

输出目录：

```text
e/976/解释/publication-receipt-packet-index-publication-receipt-packet-check
```

输出格式：

- JSON：机器可消费 contract check。
- CSV：check rows 快速查看表。
- Text：CLI 摘要。
- Markdown：人工审阅报告。
- HTML：截图证据页面。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_check.py`

这是核心 check builder。它提供：

- `locate_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet`
- `read_json_report`
- `build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_check`
- `resolve_exit_code`

主流程是：

1. 从原始 packet 里解析 `receipt_review_path`。
2. 读取 v974 receipt review。
3. 调用 v975 的 `build_*_packet()` 重建 packet。
4. 对比原始 packet 和 rebuilt packet 的 status、decision、summary、packet、rows、evidence、checks。
5. 生成 contract check report。

### `CHECKED_SUMMARY_FIELDS`

这个 tuple 定义 summary 层必须稳定的字段：

- ready key
- packet id
- packet status
- consumer name
- lookup ready
- granted use
- blocked uses
- publication index row count
- source evidence count
- consumer receipt count
- lookup key count
- promotion flags
- consumer boundary
- model quality claim
- next step

这些字段是后续 index 版本真正会消费的摘要层。

### `CHECKED_PACKET_FIELDS`

这个 tuple 定义 packet body 层必须稳定的字段：

- `packet_ready`
- `packet_id`
- `packet_status`
- `receipt_review_path`
- `receipt_review_sha256`
- `publication_receipt_path`
- `publication_receipt_sha256`
- `consumer_name`
- `consumer_boundary`
- `granted_use`
- `blocked_uses`
- source path fields
- promotion flags
- `model_quality_claim`
- `next_step`

如果有人改了 packet body 但没有同步源 review，contract check 会失败。

### `_resolve_source_review()`

这个函数先看 report 顶层的 `receipt_review_path`，再看 packet body 的 `receipt_review_path`。如果路径是相对路径，会尝试以 packet JSON 所在目录作为 sibling 解析。

这让 contract check 同时支持绝对/相对源路径，并且能在路径缺失时明确失败。

### `_rebuild_receipt_packet()`

如果源 review 不存在，它返回一个 fail-shaped rebuilt packet，而不是抛异常中断。这样输出报告仍然能说明失败原因。

如果源 review 存在，它会调用：

```python
build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet(
    read_receipt_review_json(source_review),
    receipt_review_path=source_review,
)
```

这就是本版“可重建性”的核心。

### `_check_rows()`

`_check_rows()` 先检查源 review path 是否存在，再逐项比较：

- `status`
- `decision`
- `failed_count`
- `summary.<field>`
- `packet.<field>`
- `packet_rows`
- `source_evidence_rows`
- `check_rows`

真实 v976 运行时共有 48 个 pass check。这个数量来自字段级对比，不是只做一个粗略 status check。

### `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_check_artifacts.py`

artifact writer 输出 JSON、CSV、text、Markdown、HTML。HTML 顶部展示：

- Status
- Ready
- Original use
- Rebuilt use
- Evidence
- Failed

下面展示 Contract Summary 和完整 Checks 表。

### `scripts/check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.py`

这是独立 check CLI：

```powershell
python scripts\check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.py <packet-or-dir> --out-dir <dir> --require-pass --force
```

`--require-pass` 会在 check 失败时返回非 0，适合放进 CI 或 release gate。

### `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.py`

v976 还增强了 v975 build CLI：新增 `--check-out-dir`。现在构建 packet 时可以同步生成 sidecar contract check。

这个改动放在 v976 做是合理的，因为 v975 阶段 check 模块还不存在；如果提前 import 会造成死依赖。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_check.py
```

测试覆盖：

- 可重建 packet 能通过 contract check。
- packet source path 被篡改时失败。
- source review 缺失时失败。
- `--require-pass` 对篡改 packet 返回 `SystemExit(1)`。
- artifact writer 和 check CLI 输出完整格式。
- build CLI 的 `--check-out-dir` 可以生成 sidecar contract check。

聚焦测试结果：

```text
11 passed
```

## 运行证据

正式命令：

```powershell
python scripts\check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet.py e\975\解释\publication-receipt-packet-index-publication-receipt-packet --out-dir e\976\解释\publication-receipt-packet-index-publication-receipt-packet-check --require-pass --force
```

正式摘要：

```text
status=pass
contract_check_ready=True
original_packet_status=downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_ready
rebuilt_packet_status=downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_ready
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_source_evidence_count=2
rebuilt_source_evidence_count=2
passed_check_count=48
failed_check_count=0
```

截图归档：

```text
e/976/图片/v976-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-check.png
```

## 一句话总结

v976 把 v975 packet 从“已生成”推进到“可从源 review 重建并逐字段一致”，为下一步 packet index 提供了更可信的输入边界。

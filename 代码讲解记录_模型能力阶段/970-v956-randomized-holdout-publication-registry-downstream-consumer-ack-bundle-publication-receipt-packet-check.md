# v956 randomized holdout publication registry downstream consumer ack bundle publication receipt packet check

## 本版目标与边界

v956 的目标是检查 v955 receipt packet 是否能从 v954 receipt review 重建出来。v955 已经把 receipt review 打包成 packet；v956 负责验证这个 packet 没有被篡改，尤其是 lookup key、granted use、packet rows 和 no-promotion 字段。

这版不生成新训练结果，不扩大模型质量声称，也不批准 production promotion。它只是 contract check：重建一次 v955 packet，并比较稳定字段。

前置链路：

```text
v954 publication receipt review
 -> v955 publication receipt packet
 -> v956 publication receipt packet contract check
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check.py`
  - v956 核心 contract check。
  - 从 packet 里解析 `receipt_review_path`，读取 v954 review，重新调用 v955 builder，然后比较原始 packet 与重建 packet。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 输出每条比较检查，HTML 展示 source review、original/rebuilt lookup keys 和全部检查。

- `scripts/check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.py`
  - v956 CLI。
  - 支持输入 packet JSON 或输出目录，`--require-pass` 下失败返回 1。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_check.py`
  - 覆盖可重建 packet、lookup key 篡改、source review 缺失、CLI 失败退出、artifact 输出。

- `e/956/解释/randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check/`
  - 使用真实 v955 packet 生成的运行证据。

## 核心数据结构

v956 不新增业务 packet，而是输出 check report：

```python
{
    "status": "pass",
    "decision": "randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_contract_check_passed",
    "source_receipt_packet": "...v955...json",
    "source_receipt_review": "...v954...json",
    "source_summary": {...},
    "rebuilt_summary": {...},
    "source_packet": {...},
    "rebuilt_packet": {...},
    "source_packet_rows": [...],
    "rebuilt_packet_rows": [...],
    "check_rows": [...],
}
```

`source_*` 字段来自 v955 原始 packet，`rebuilt_*` 字段来自重新运行 v955 builder 的结果。只有两边稳定字段完全一致时，`contract_check_ready=True`。

## 比较字段

`CHECKED_SUMMARY_FIELDS` 包含：

- packet ready 标记、packet id、packet status。
- consumer、lookup ready、granted use、blocked uses。
- publication/source evidence/consumer receipt/lookup key 计数。
- promotion、approved for promotion、consumer boundary、model quality claim。
- next step。

`CHECKED_PACKET_FIELDS` 包含：

- packet body 的 ready/id/status。
- `receipt_review_path` 与 `receipt_review_sha256`。
- `publication_receipt_path` 与 `publication_receipt_sha256`。
- consumer、boundary、granted use、blocked uses。
- row counts、lookup keys、source index review、source publication、source publication check。
- promotion、approved for promotion、model quality claim、next step。

最后还整体比较 `packet_rows`，防止 CSV/HTML 消费层和 JSON body 不一致。

## CLI 运行流程

真实命令：

```powershell
python scripts\check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet.py e\955\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet --out-dir e\956\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check --require-pass --force
```

流程：

1. 定位 v955 receipt packet JSON。
2. 从 packet 里读取 `receipt_review_path`。
3. 读取 v954 receipt review。
4. 调用 v955 builder 重建 packet。
5. 比较 status、decision、failed count、summary 字段、packet body 字段和 packet rows。
6. 输出 check JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 5 个场景：

- 可重建的 ready packet 通过 contract check。
- packet lookup key 被篡改时失败。
- source receipt review 缺失时失败。
- CLI 在 `--require-pass` 下对篡改 packet 返回 1。
- artifact writer 和 CLI 输出完整。

这组测试保护 v955 packet 不会在下游索引前被静默改动。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_contract_check_passed
failed_count=0
contract_check_ready=True
original_packet_status=downstream_publication_receipt_packet_ready
rebuilt_packet_status=downstream_publication_receipt_packet_ready
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=44
failed_check_count=0
```

Playwright MCP 截图：

```text
e/956/图片/v956-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-check.png
```

## 一句话总结

v956 证明 v955 receipt packet 可以从 v954 review 完整重建，给后续索引加上了防篡改契约检查。

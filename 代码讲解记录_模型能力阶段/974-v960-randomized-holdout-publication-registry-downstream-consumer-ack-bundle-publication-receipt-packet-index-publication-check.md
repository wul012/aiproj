# v960 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication check

## 本版目标与边界

v960 的目标是给 v959 receipt packet index publication 增加 contract check：读取 v959 publication，定位它记录的 v958 review，然后重新构建 publication，并比较稳定字段。

这版不生成新的 publication，不训练模型，不批准 promotion。它只验证“已发布 artifact 是否可从源 review 重建”。

前置链路：

```text
v957 receipt packet index
 -> v958 receipt packet index review
 -> v959 receipt packet index publication
 -> v960 receipt packet index publication contract check
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.py`
  - v960 核心 contract check。
  - 从 v959 publication 中解析 `receipt_packet_index_review_path`，重新调用 v959 builder，并比较 summary/publication 稳定字段。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 original/rebuilt use、publication status、row count 和检查表。

- `scripts/check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.py`
  - v960 CLI。
  - 支持 `--require-pass` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_check.py`
  - 覆盖可重建 publication、用途篡改、源 review 缺失、CLI 失败退出和 artifact 输出。

- `e/960/解释/receipt-packet-index-publication-check/`
  - 使用真实 v959 publication 生成的运行证据。

## 核心数据结构

contract check 输出保留原始与重建两组结构：

```python
{
    "original_summary": {...},
    "rebuilt_summary": {...},
    "original_publication": {...},
    "rebuilt_publication": {...},
    "summary": {
        "contract_check_ready": True,
        "original_publication_status": "published_for_downstream_receipt_packet_index_lookup_only",
        "rebuilt_publication_status": "published_for_downstream_receipt_packet_index_lookup_only",
        "original_published_use": "downstream_governance_lookup_only",
        "rebuilt_published_use": "downstream_governance_lookup_only",
        "original_packet_index_row_count": 1,
        "rebuilt_packet_index_row_count": 1,
        "next_step": "index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication",
    }
}
```

这个结构的作用是把 publication 的可复核性显式化。后续 index 不需要盲目信任 v959 JSON，而可以先消费 v960 check。

## 核心检查逻辑

`_checks()` 先做基础检查：

- `source_receipt_packet_index_review_exists`：v958 review 必须存在。
- `status`、`decision`、`failed_count`：原始 publication 和重建 publication 必须一致。
- `check_rows`：v959 生成 publication 时的检查表必须可重建。

随后对 `SUMMARY_FIELDS` 做逐字段比较：

- ready 标志、publication id/status、consumer、published use。
- publish/lookup/contract ready。
- packet index row count、source packet row count、source evidence count。
- promotion/approved、consumer boundary、model quality claim。

再对 `PUBLICATION_FIELDS` 做逐字段比较：

- source review、source index、source packet、source packet check 路径。
- published use、ready 标志、计数、no-promotion 字段。
- `next_step` 必须仍指向下一步 index。

## CLI 运行流程

真实命令：

```powershell
python scripts\check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication.py e\959\解释\randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication --out-dir e\960\解释\receipt-packet-index-publication-check --require-pass --force
```

流程：

1. 定位 v959 publication JSON。
2. 从 publication 中解析 v958 review 路径。
3. 读取 v958 review 并重新构建 publication。
4. 比较 status、decision、failed count、check rows、summary 字段和 publication 字段。
5. 输出 contract check JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

新增测试覆盖 5 个场景：

- ready publication 可以从源 review 重建并通过 contract check。
- publication use 被篡改时 summary/publication 字段检查失败。
- 源 review 缺失时失败。
- CLI 在 `--require-pass` 下对篡改 publication 返回 1。
- artifact writer 和 CLI 输出完整。

这组测试保护后续 index 不能消费被篡改或失去源 review 的 publication。

## 运行证据

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_contract_check_passed
failed_count=0
contract_check_ready=True
original_publication_status=published_for_downstream_receipt_packet_index_lookup_only
rebuilt_publication_status=published_for_downstream_receipt_packet_index_lookup_only
original_published_use=downstream_governance_lookup_only
rebuilt_published_use=downstream_governance_lookup_only
original_packet_index_row_count=1
rebuilt_packet_index_row_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=40
failed_check_count=0
```

Playwright MCP 截图：

```text
e/960/图片/v960-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-check.png
```

## 一句话总结

v960 把 v959 publication 变成可重建、可审计、可索引前验证的 lookup-only 发布产物。

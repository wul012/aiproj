# v967 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index

## 本版目标与边界

v967 的目标是把 v965 receipt packet 与 v966 contract check 合成一个 receipt packet index。v965 提供 packet rows 与 source evidence rows，v966 证明 packet 可从 v964 review 重建。v967 将两者绑定成 lookup-only index，供下一步 review 使用。

这版不训练模型，不扩大模型质量声明，不批准 production promotion。它只把已经通过 contract check 的 packet 变成可检索索引。

前置链路：

```text
v965 receipt packet
 -> v966 receipt packet contract check
 -> v967 receipt packet index
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.py`
  - v967 核心 index builder。
  - 读取 v965 packet 和 v966 check。
  - 校验 packet/check 状态一致、lookup-only、source evidence 存在、上游 source artifacts 存在、no-promotion 不漂移。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 写 index row；HTML 展示 lookup boundary、index rows、source evidence 和 checks。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.py`
  - v967 CLI。
  - 支持 `--receipt-packet`、`--receipt-packet-check`、`--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.py`
  - 覆盖 ready index、contract check 失败、source review 丢失、CLI require-index-ready 失败返回和 artifact 输出。

- `e/967/解释/publication-receipt-packet-index/`
  - 使用真实 v965/v966 生成的运行证据。

## 核心数据结构

`receipt_packet_index` 是主结构：

```python
{
    "index_ready": True,
    "receipt_packet_index_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-v967",
    "lookup_scope": "downstream_governance_lookup_only",
    "receipt_packet_index_rows": [...],
    "source_packet_rows": [...],
    "source_evidence_rows": [...],
    "source_evidence_count": 2,
    "lookup_ready": True,
    "contract_check_ready": True,
    "promotion_ready": False,
    "next_step": "review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index",
}
```

单条 `receipt_packet_index_rows` 包含：

```python
{
    "lookup_key": "publication:...",
    "packet_id": "...v965",
    "packet_status": "downstream_receipt_packet_index_publication_receipt_packet_ready",
    "consumer_name": "publication_registry_governance_lookup_reader",
    "granted_use": "downstream_governance_lookup_only",
    "source_packet_path": "...v965 json...",
    "source_packet_check_path": "...v966 json...",
    "source_evidence_count": 2,
    "contract_check_ready": True,
    "promotion_ready": False,
}
```

## 29 项检查

`_checks()` 保护以下边界：

- v965 packet 与 v966 check 文件存在。
- packet status/decision/summary/body 都 ready。
- contract check status/decision/summary 都 ready。
- packet status 与 v966 original/rebuilt packet status 一致。
- granted use 仍是 downstream governance lookup only。
- lookup_ready 成立。
- packet row 刚好 1 条。
- source evidence rows 刚好 2 条、status 全 pass、文件全存在。
- lookup key 保持 `publication:` namespace。
- source receipt review、source publication receipt、source index review、source publication、source publication check、source review、source index 都存在。
- consumer boundary 与 model quality claim 保守。
- packet 与 check 的 promotion_ready 都是 false。
- v965/v966 failed_check_count 都为 0。
- v965 next step 指向 check，v966 next step 指向 index。

这保证 v967 不是把两个 JSON 粘在一起，而是确认它们确实构成可继续 review 的 lookup-only index。

## 测试覆盖

聚焦测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_check.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.py -q -o cache_dir=runs\pytest-cache-v967-focus
```

结果：

```text
11 passed
```

全量验证：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v967-full
```

结果：

```text
2204 passed
```

Source encoding hygiene：

```text
status=pass, source_count=1730, syntax_error_count=0
```

测试保护的关键行为：

- 合法 packet + check 可以生成 index。
- contract check 失败会阻断 index ready。
- source review 路径丢失会阻断 index ready。
- `--require-index-ready` 遇到篡改 packet 返回 1。
- CLI 和 JSON/CSV/TXT/Markdown/HTML 输出完整。

## 运行证据

真实 v967 evidence 来自 v965/v966：

```text
status=pass
failed_count=0
receipt_packet_index_row_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=29
failed_check_count=0
```

Playwright MCP 打开 HTML 报告并保存：

- `e/967/解释/v967-playwright-snapshot.md`
- `e/967/图片/v967-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index.png`

## 一句话总结

v967 把 v965/v966 的 receipt packet 与 contract check 收束成一个可 review 的 lookup-only index，继续保持 promotion 关闭。

# v972 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication index review

## 本版目标与边界

v972 的目标是审查 v971 的 lookup-only publication index，并判断它是否可以进入下一步 receipt 记录。v971 已经把 v969 publication 与 v970 contract check 收束成一行 index；v972 则验证这行 index 是否具备 downstream receipt recording 的条件。

本版不训练模型，不改变模型权重，不扩大模型质量声明，不批准 production promotion。它只允许在 governance lookup 边界内记录 receipt。

前置链路：

```text
v969 publication
 -> v970 publication contract check
 -> v971 publication index
 -> v972 publication index review
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_review.py`
  - v972 核心 review builder。
  - 读取 v971 index，检查 index ready、lookup scope、source paths、row count、lookup key namespace 和 no-promotion。
- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_review_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 review boundary、source paths 和 check rows。
- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_review.py`
  - v972 CLI。
  - 支持输入 v971 index JSON 或目录，支持 `--require-review-ready`、`--require-downstream-ready`、`--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_review.py`
  - 覆盖 ready review、source publication 缺失、published use 漂移、CLI require-review-ready 失败退出、输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v972 下一步：`record_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt`。
- `src/minigpt/__init__.py`
  - 接入 v972 build/write lazy export。

## 核心数据结构

`review` 是 v972 的主结构：

```python
{
    "review_ready": True,
    "review_id": "...index-review-v972",
    "review_status": "approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt",
    "publication_index_path": "...v971 json...",
    "publication_index_row_count": 1,
    "lookup_keys": ["publication:<publication_id>"],
    "downstream_ready": True,
    "lookup_ready": True,
    "contract_check_ready": True,
    "receipt_ready": True,
    "allowed_use": "downstream_governance_lookup_only",
    "blocked_uses": [...],
    "source_publication_path": "...v969 json...",
    "source_publication_check_path": "...v970 json...",
    "source_review_path": "...v968 json...",
    "source_index_path": "...v967 json...",
    "promotion_ready": False,
    "next_step": "record_...",
}
```

这个结构说明 v972 的批准范围很窄：只允许下游记录治理 receipt，不允许生产使用。

## 20 项检查保护什么

`_checks()` 覆盖：

- v971 index 文件存在。
- index status 和 decision ready。
- summary/body 都标记 index ready。
- lookup scope 与 published use 都是 downstream governance lookup only。
- lookup_ready 与 contract_check_ready 都为 true。
- publication index rows 恰好 1 行。
- lookup key 使用 `publication:` namespace。
- index row 不能 promotion。
- source publication、source publication check、source review、source index 文件都存在。
- consumer boundary 与 model quality claim 保守。
- promotion_ready 和 approved_for_promotion 都为 false。
- source failed_check_count 为 0。
- v971 next step 必须指向 v972 review。

这些检查的目的不是证明模型更强，而是证明证据链没有断、用途没有变宽、后续 receipt 有稳定输入。

## 测试覆盖

焦点测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_review.py -q -o cache_dir=runs\pytest-cache-v972-focus
```

结果：

```text
9 passed
```

关键断言：

- ready v971 index 能通过 review。
- source publication 缺失会失败。
- `published_use` 漂移到 `production_promotion` 会失败。
- 篡改 next step 时 `--require-review-ready` 返回 `1`。
- JSON/CSV/TXT/Markdown/HTML 输出可用。

全量测试：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v972-full
```

结果：

```text
2228 passed
```

Source encoding hygiene：

```text
status=pass, source_count=1750, bom_count=0, syntax_error_count=0
```

## 运行证据

真实 evidence 命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_review.py e\971\解释\publication-receipt-packet-index-publication-index --out-dir e\972\解释\publication-receipt-packet-index-publication-index-review --require-review-ready --require-downstream-ready --force
```

关键输出：

```text
status=pass
review_status=approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt
downstream_ready=True
receipt_ready=True
allowed_use=downstream_governance_lookup_only
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

Playwright MCP 截图和快照：

- `e/972/图片/v972-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-index-review.png`
- `e/972/解释/v972-playwright-snapshot.md`

## 一句话总结

v972 把 v971 lookup-only index 审核为可记录 receipt 的下游治理输入，同时继续明确不允许生产 promotion。

# v962 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication index review

## 本版目标与边界

v962 的目标是 review v961 生成的 `receipt packet index publication index`。v961 已经把 v959 publication 和 v960 contract check 合并成 lookup-only index，v962 再确认这个 index 本身可以进入 receipt recording。

这版解决的问题是：如果 v961 index 后续被篡改、source path 丢失、lookup-only 使用范围漂移，或 next step 被改错，receipt 层不能盲目接收它。

本版不做模型训练，不扩大模型质量声明，不批准 production promotion。它只是给 v961 index 加一层 receipt 前置复核。

前置链路：

```text
v959 receipt packet index publication
 -> v960 receipt packet index publication contract check
 -> v961 receipt packet index publication index
 -> v962 receipt packet index publication index review
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.py`
  - v962 核心 review builder。
  - 读取 v961 index JSON，检查 status、decision、summary/body ready、lookup scope、published use、source 文件存在、next step 和 promotion 边界。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review_artifacts.py`
  - 负责 JSON、CSV、TXT、Markdown、HTML 输出。
  - HTML 展示 review boundary 与 checks；CSV 保留每条检查，便于后续机器读取。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.py`
  - v962 CLI。
  - 支持输入 v961 JSON 文件或 v961 输出目录。
  - 支持 `--require-review-ready`、`--require-downstream-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.py`
  - 覆盖 ready review、source publication 丢失、published use 漂移、CLI require 失败、artifact/locator 输出。

- `e/962/解释/receipt-packet-index-publication-index-review/`
  - 使用真实 v961 evidence 生成的 v962 运行证据。

## 核心输入输出

输入是 v961 的 index report：

```python
{
    "status": "pass",
    "decision": "..._publication_index_ready",
    "summary": {
        "..._publication_index_ready": True,
        "lookup_scope": "downstream_governance_lookup_only",
        "published_use": "downstream_governance_lookup_only",
        "publication_index_row_count": 1,
        "lookup_ready": True,
        "contract_check_ready": True,
        "promotion_ready": False,
        "next_step": "review_...",
    },
    "publication_index": {
        "index_ready": True,
        "publication_index_rows": [...],
        "publication_path": "...",
        "publication_check_path": "...",
        "source_review_path": "...",
        "source_index_path": "...",
    },
}
```

输出的核心结构是 `review`：

```python
{
    "review_ready": True,
    "review_id": "randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-index-review-v962",
    "review_status": "approved_for_downstream_receipt_packet_index_publication_receipt",
    "publication_index_row_count": 1,
    "lookup_keys": ["publication:..."],
    "downstream_ready": True,
    "lookup_ready": True,
    "contract_check_ready": True,
    "receipt_ready": True,
    "promotion_ready": False,
    "allowed_use": "downstream_governance_lookup_only",
    "next_step": "record_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt",
}
```

这里的 `receipt_ready=True` 只表示可以记录 lookup-only receipt，不表示模型可晋升，也不表示生产可用。

## 20 项检查

`_checks()` 是本版最重要的保护层：

- `publication_index_file_exists`：v961 index 文件必须存在。
- `publication_index_passed`：源 report 顶层 status 必须是 `pass`。
- `publication_index_decision_ready`：源 decision 必须是 v961 ready decision。
- `publication_index_summary_ready`：summary ready 与 body `index_ready` 必须同时为 true。
- `lookup_scope_downstream`：summary/body lookup scope 必须都是 downstream lookup-only。
- `published_use_lookup_only`：published use 不能漂移到 production promotion。
- `lookup_ready`：lookup ready 必须在 summary/body 中同时成立。
- `contract_check_ready`：contract check ready 必须在 summary/body 中同时成立。
- `publication_index_rows_present`：publication index row 必须刚好 1 条。
- `lookup_keys_present`：lookup key 必须使用 `publication:` namespace。
- `publication_index_rows_not_promoted`：index row 不能含 promotion。
- `source_publication_file_exists`、`source_publication_check_file_exists`、`source_review_file_exists`、`source_index_file_exists`：上游 source 文件必须仍可追溯。
- `consumer_boundary_governance`：consumer boundary 必须保持 governance lookup only。
- `model_quality_claim_bounded`：model quality claim 必须保持 bounded。
- `promotion_still_false`：summary/body/approved 都不能开启 promotion。
- `source_checks_clean`：v961 failed check count 必须为 0。
- `source_next_step_matches`：v961 next step 必须指向 v962 review。

这些检查把“能记录 receipt”的条件压到源 artifact 的稳定字段上，而不是相信文件名或目录名。

## CLI 与退出码

CLI 的正常运行命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.py e\961\解释\receipt-packet-index-publication-index --out-dir e\962\解释\receipt-packet-index-publication-index-review --require-review-ready --require-downstream-ready --force
```

`--require-review-ready` 会在 review 未通过时返回 1。`--require-downstream-ready` 会要求 downstream receipt 前置条件成立。`--require-promotion-ready` 仍会返回 1，因为本链路明确不批准 promotion。

## 测试覆盖

本版新增 5 个测试：

- ready index 可以得到 `status=pass`、review ready、receipt ready、allowed use lookup-only。
- source publication 路径被改成不存在时，必须出现 `source_publication_file_exists` failure。
- `published_use` 被改成 `production_promotion` 时，必须出现 `published_use_lookup_only` failure。
- CLI 在 tampered index 上加 `--require-review-ready` 必须返回 1。
- artifact 输出与 locator 能正常处理“文件路径”和“输出目录”两种输入。

聚焦测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.py -q -o cache_dir=runs\pytest-cache-v962-focus
```

结果：

```text
9 passed
```

全量验证：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v962-full
```

结果：

```text
2179 passed
```

## 运行证据

真实证据来自 v961：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_index_review.py e\961\解释\receipt-packet-index-publication-index --out-dir e\962\解释\receipt-packet-index-publication-index-review --require-review-ready --require-downstream-ready --force
```

关键输出：

```text
status=pass
failed_count=0
review_status=approved_for_downstream_receipt_packet_index_publication_receipt
publication_index_row_count=1
downstream_ready=True
receipt_ready=True
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

Playwright MCP 打开 HTML 报告并保存：

- `e/962/解释/v962-playwright-snapshot.md`
- `e/962/图片/v962-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-index-review.png`

## 一句话总结

v962 把 v961 publication index 从“可以被查询”推进到“可以被记录 lookup-only receipt”，并继续把 promotion 和模型质量扩张挡在链路外。

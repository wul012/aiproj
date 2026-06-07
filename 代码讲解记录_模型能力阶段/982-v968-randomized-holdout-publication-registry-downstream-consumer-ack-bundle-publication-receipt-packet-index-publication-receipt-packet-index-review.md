# v968 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index review

## 本版目标与边界

v968 的目标是 review v967 receipt packet index。v967 已经把 v965 packet 和 v966 contract check 合成 lookup-only index，v968 检查这个 index 是否可以进入下一步 publication。

这版不训练模型，不扩大模型质量声明，不批准 production promotion。review 的通过只表示可以做 lookup-only publication。

前置链路：

```text
v965 receipt packet
 -> v966 receipt packet contract check
 -> v967 receipt packet index
 -> v968 receipt packet index review
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review.py`
  - v968 核心 review builder。
  - 读取 v967 index，检查 lookup scope、contract-check readiness、source evidence、source packet/check 文件存在和 no-promotion。

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 review boundary 和 check rows。

- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review.py`
  - v968 CLI。
  - 支持 `--require-review-ready`、`--require-downstream-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review.py`
  - 覆盖 ready review、source evidence 缺失、lookup use 漂移、CLI require-review-ready 失败返回和 artifact 输出。

- `e/968/解释/publication-receipt-packet-index-review/`
  - 使用真实 v967 index 生成的运行证据。

## 核心数据结构

`review` 是主结构：

```python
{
    "review_ready": True,
    "review_id": "...v968",
    "review_status": "approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication",
    "receipt_packet_index_row_count": 1,
    "source_packet_row_count": 1,
    "source_evidence_count": 2,
    "downstream_ready": True,
    "publish_ready": True,
    "lookup_ready": True,
    "contract_check_ready": True,
    "promotion_ready": False,
    "allowed_use": "downstream_governance_lookup_only",
    "next_step": "publish_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index",
}
```

这里的 `publish_ready=True` 只允许进入 lookup-only publication，不等价于 promotion-ready。

## 23 项检查

`_checks()` 保护以下边界：

- v967 index 文件存在，status/decision ready。
- summary 和 body 都 index_ready。
- lookup scope 与 granted use 都是 downstream governance lookup only。
- lookup_ready 与 contract_check_ready 都成立。
- receipt packet index row 为 1 条，source packet row 为 1 条。
- lookup key 使用 `publication:` namespace。
- index rows 和 source packet rows 均不 promotion。
- source evidence rows 为 2 条、status 全 pass、文件全存在。
- source packet 与 source packet check 文件存在。
- consumer boundary 与 model quality claim 保守。
- promotion_ready 和 approved_for_promotion 都为 false。
- v967 failed_check_count 为 0。
- v967 next step 必须指向 v968 review。

## 测试覆盖

聚焦测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_review.py -q -o cache_dir=runs\pytest-cache-v968-focus
```

结果：

```text
10 passed
```

全量验证：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v968-full
```

结果：

```text
2209 passed
```

Source encoding hygiene：

```text
status=pass, source_count=1734, syntax_error_count=0
```

测试保护的关键行为：

- 合法 v967 index 可以 review ready。
- source evidence path 缺失会失败。
- granted use 漂移为 production promotion 会失败。
- `--require-review-ready` 遇到篡改 index 返回 1。
- CLI 和 JSON/CSV/TXT/Markdown/HTML 输出完整。

## 运行证据

真实 v968 evidence 来自 v967：

```text
status=pass
failed_count=0
review_status=approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication
source_evidence_count=2
downstream_ready=True
publish_ready=True
promotion_ready=False
passed_check_count=23
failed_check_count=0
```

Playwright MCP 打开 HTML 报告并保存：

- `e/968/解释/v968-playwright-snapshot.md`
- `e/968/图片/v968-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-review.png`

## 一句话总结

v968 把 v967 receipt packet index 推进到 lookup-only publication 前的 review-ready 状态，继续保持 promotion 关闭。

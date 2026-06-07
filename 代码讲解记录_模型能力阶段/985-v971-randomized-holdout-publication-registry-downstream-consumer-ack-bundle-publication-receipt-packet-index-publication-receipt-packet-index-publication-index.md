# v971 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication index

## 本版目标与边界

v971 的目标是把 v969 lookup-only publication 和 v970 contract check 整理成一个下游可查询的 publication index。v969 负责发布，v970 负责重建验证，v971 则把两者合并成一行可审计索引。

本版不训练模型，不改变 checkpoint，不扩大模型质量声明，不批准 production promotion。它只建立 lookup-only index，后续版本仍需要 review，不能直接进入生产 promotion。

前置链路：

```text
v969 receipt packet index publication
 -> v970 receipt packet index publication contract check
 -> v971 receipt packet index publication index
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.py`
  - v971 核心 index builder。
  - 输入 v969 publication 和 v970 check，检查两边状态、lookup-only scope、row count、源路径和 no-promotion。
- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 只写 publication index rows，HTML 同时展示 lookup boundary 和 checks。
- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.py`
  - v971 CLI。
  - 支持 `--publication`、`--publication-check`、`--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.py`
  - 覆盖 ready index、contract check failed、published use drift、CLI/artifact 输出。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v971 下一步：`review_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index`。
- `src/minigpt/__init__.py`
  - 接入 v971 build/write lazy export。

## 核心数据结构

`publication_index` 是本版主结构：

```python
{
    "index_ready": True,
    "publication_index_id": "...index-v971",
    "lookup_scope": "downstream_governance_lookup_only",
    "publication_index_rows": [
        {
            "publication_index_id": "...index-v971",
            "lookup_key": "publication:<publication_id>",
            "publication_id": "...v969",
            "publication_status": "...lookup_only",
            "published_use": "downstream_governance_lookup_only",
            "source_publication_path": "...v969 json...",
            "source_publication_check_path": "...v970 json...",
            "receipt_packet_index_row_count": 1,
            "source_packet_row_count": 1,
            "contract_check_ready": True,
            "promotion_ready": False,
        }
    ],
    "lookup_ready": True,
    "contract_check_ready": True,
    "promotion_ready": False,
    "next_step": "review_...",
}
```

这一行 index 不是模型质量提升证据，而是治理查找入口。后续 review 或 receipt 可以从 `lookup_key` 找到 publication，并沿着 `source_publication_path` 与 `source_publication_check_path` 回查完整证据。

## 24 项检查保护什么

`_checks()` 保护以下边界：

- v969 publication 文件存在且 `status=pass`。
- v969 publication decision 是 ready。
- v970 contract check 文件存在且 `status=pass`。
- v970 decision 是 contract check passed。
- contract check ready 为 true。
- publication status 与 v970 original/rebuilt status 一致。
- published use 在 publication、original check、rebuilt check 中都保持 lookup-only。
- lookup_ready 为 true。
- receipt packet index row count 在 publication、original check、rebuilt check 中都为 1。
- source packet row count 都为 1。
- source evidence count 为 2。
- source review/index/packet/packet check 文件仍存在。
- consumer boundary 和 model quality claim 保守。
- promotion_ready、original_promotion_ready、rebuilt_promotion_ready 都为 false。
- publication 与 contract check 的 failed_check_count 都为 0。
- publication next step 指向 v970 check，check next step 指向 v971 index。

这些断言保证 v971 index 不是“只把 JSON 放进表”，而是把 publication 和 contract check 两条证据链合并校验后再落表。

## 测试覆盖

焦点测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.py -q -o cache_dir=runs\pytest-cache-v971-focus
```

结果：

```text
9 passed
```

关键测试包括：

- ready publication + ready contract check 可以生成 1 行 index。
- contract check 失败会阻断 index ready。
- `published_use` 被改成 `production_promotion` 会失败。
- CLI 能从目录定位 publication/check JSON。
- JSON/CSV/TXT/Markdown/HTML 输出完整。

全量测试：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v971-full
```

结果：

```text
2223 passed
```

Source encoding hygiene：

```text
status=pass, source_count=1746, bom_count=0, syntax_error_count=0
```

## 运行证据

真实 evidence 命令：

```powershell
python scripts\build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_index.py --publication e\969\解释\publication-receipt-packet-index-publication --publication-check e\970\解释\publication-receipt-packet-index-publication-check --out-dir e\971\解释\publication-receipt-packet-index-publication-index --require-index-ready --require-lookup-ready --force
```

关键输出：

```text
status=pass
publication_index_row_count=1
lookup_scope=downstream_governance_lookup_only
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=24
failed_check_count=0
```

Playwright MCP 截图和快照：

- `e/971/图片/v971-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-index.png`
- `e/971/解释/v971-playwright-snapshot.md`

## 一句话总结

v971 把 v969 publication 和 v970 contract check 合并为 lookup-only index，使后续 review 可以从单一索引入口读取已发布且已复核的治理证据。

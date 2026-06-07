# v970 randomized holdout publication registry downstream consumer ack bundle publication receipt packet index publication receipt packet index publication check

## 本版目标与边界

v970 的目标是给 v969 的 lookup-only publication 增加一层 contract check。v969 已经把 v968 receipt packet index review 发布成下游可查询的 publication；v970 负责验证这份 publication 是否还能从它记录的源 review 重新推导出来。

本版不训练模型，不改 checkpoint，不声明模型能力提升，不批准 production promotion。它只验证治理证据链的可复核性：publication 的关键字段必须与重建结果一致，lookup-only 边界必须保持，promotion 必须继续为 false。

前置链路：

```text
v968 receipt packet index review
 -> v969 receipt packet index publication
 -> v970 receipt packet index publication contract check
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check.py`
  - v970 核心 contract check。
  - 输入 v969 publication JSON，解析其中的 `receipt_packet_index_review_path`，重新调用 v969 publication builder，然后比较原始结果和重建结果。
- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 报告用于 Playwright MCP 截图，CSV 用于逐项检查行审阅。
- `scripts/check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.py`
  - v970 CLI。
  - 支持输入 publication JSON 或 publication 输出目录，支持 `--require-pass` 和 `--force`。
- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check.py`
  - 覆盖 rebuild pass、publication use 篡改、源 review 丢失、CLI require-pass 失败退出、输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v970 通过后的下一步路由 `index_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication`。
- `src/minigpt/__init__.py`
  - 接入 v970 build/write 的 lazy export。

## 核心数据结构

v970 报告的关键结构如下：

```python
{
    "status": "pass",
    "decision": "...contract_check_passed",
    "failed_count": 0,
    "publication_path": "...v969 json...",
    "source_receipt_packet_index_review": "...v968 json...",
    "original_summary": {...},
    "rebuilt_summary": {...},
    "original_publication": {...},
    "rebuilt_publication": {...},
    "check_rows": [...],
    "summary": {
        "contract_check_ready": True,
        "original_publication_status": "...lookup_only",
        "rebuilt_publication_status": "...lookup_only",
        "original_published_use": "downstream_governance_lookup_only",
        "rebuilt_published_use": "downstream_governance_lookup_only",
        "original_receipt_packet_index_row_count": 1,
        "rebuilt_receipt_packet_index_row_count": 1,
        "original_promotion_ready": False,
        "rebuilt_promotion_ready": False,
        "next_step": "index_...",
    },
}
```

`original_*` 来自 v969 文件本身；`rebuilt_*` 来自重新读取 v968 review 后再次运行 v969 builder。只有两者一致，contract check 才能通过。

## 运行流程

1. `locate_randomized_holdout_..._publication()` 接受文件或目录。
2. `read_json_report()` 读取 v969 publication JSON。
3. `_resolve_source_review_path()` 从 report 或 publication body 中找到 `receipt_packet_index_review_path`。
4. `_rebuild_publication()` 重新读取 v968 review，并调用 v969 builder。
5. `_checks()` 比较原始 report 与 rebuilt report：
   - `status`
   - `decision`
   - `failed_count`
   - `check_rows`
   - summary 字段
   - publication 字段
6. `_summary()` 输出 contract check 的决策摘要和下一步路由。

这条流程的关键点是：v970 不相信 v969 JSON 的单边声明，而是要求它能从源 review 重新生成。

## 40 项检查保护什么

v970 的 40 个 check 分三组：

- 源 review 存在性与整体一致性：
  - 源 review 文件存在。
  - status、decision、failed_count、check_rows 可以重建一致。
- summary 字段一致性：
  - ready flag、publication_id、publication_status、published_use、lookup_ready、contract_check_ready、row count、source evidence count、promotion flags、consumer boundary、model quality claim。
- publication body 一致性：
  - publication_ready、receipt_packet_index_review_path、receipt_packet_index_path、source_packet_path、source_packet_check_path、published_use、next_step 等。

如果有人手动改了 v969 publication 的 `published_use`、`next_step`、row count 或 promotion flag，v970 会把原始字段和重建字段比较出来，并在 `issues` 中保留失败行。

## 测试覆盖

焦点测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.py tests\test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_check.py -q -o cache_dir=runs\pytest-cache-v970-focus
```

结果：

```text
10 passed
```

核心断言包括：

- ready publication 可以 rebuild 并通过 contract check。
- 篡改 `published_use` 会失败。
- 删除或改错 `receipt_packet_index_review_path` 会失败。
- `--require-pass` 在失败报告下返回 `1`。
- JSON/CSV/TXT/Markdown/HTML 输出和 CLI 都可用。

全量测试：

```powershell
python -m pytest -q -o cache_dir=runs\pytest-cache-v970-full
```

结果：

```text
2219 passed
```

Source encoding hygiene：

```text
status=pass, source_count=1742, bom_count=0, syntax_error_count=0
```

## 运行证据

真实 evidence 使用 v969 publication 生成：

```powershell
python scripts\check_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication.py e\969\解释\publication-receipt-packet-index-publication --out-dir e\970\解释\publication-receipt-packet-index-publication-check --require-pass --force
```

关键输出：

```text
status=pass
failed_count=0
contract_check_ready=True
passed_check_count=40
failed_check_count=0
original_published_use=downstream_governance_lookup_only
rebuilt_published_use=downstream_governance_lookup_only
original_promotion_ready=False
rebuilt_promotion_ready=False
```

Playwright MCP 截图和快照：

- `e/970/图片/v970-randomized-holdout-publication-registry-downstream-consumer-ack-bundle-publication-receipt-packet-index-publication-receipt-packet-index-publication-check.png`
- `e/970/解释/v970-playwright-snapshot.md`

这些证据不是训练结果，而是 v970 contract check 的运行证明。后续版本可以读取 v970 JSON，确认 v969 publication 通过重建验证后再进入 index。

## 一句话总结

v970 把 v969 的 lookup-only publication 从“可发布”推进到“可重建验证”，为后续下游 index 提供了更稳的契约入口。

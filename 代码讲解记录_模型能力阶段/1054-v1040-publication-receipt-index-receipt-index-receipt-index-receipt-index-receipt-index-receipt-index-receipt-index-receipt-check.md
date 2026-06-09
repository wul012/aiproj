# v1040 publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt check 代码讲解

## 本版目标和边界

v1040 的目标是 contract-check v1039 lookup-only receipt。

v1039 已经把 v1038-reviewed receipt index 记录成 downstream lookup-only receipt。v1040 不继续新增消费层，而是从 v1039 receipt 中保存的 `receipt_index_review_path` 找回 v1038 review，重新调用 v1039 builder，再比较原始 receipt 与重建 receipt 的稳定字段。

本版不训练模型，不改变 checkpoint，不扩大模型质量声明，也不允许 production promotion。

## 前置链路

v1040 读取：

```text
e/1039/解释/receipt-v1039/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039.json
```

这份 receipt 内部指向：

```text
e/1038/解释/receipt-index-review-v1038/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038.json
```

v1040 的核心问题是：如果只拿 v1038 review 重建一次 v1039 receipt，结果是否仍然和归档里的 v1039 receipt 一致。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040.py`
  - v1040 contract check 核心模块。
  - 读取原始 receipt，解析 source review，重建 receipt，再比较字段。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1040.py`
  - CLI 入口。
  - 支持目录输入，自动定位 v1039 receipt JSON。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040.py`
  - 覆盖 rebuild pass、granted use 篡改、source review 缺失、source digest 篡改、CLI failure exit 和 artifact 输出。
- `e/1040/解释/receipt-check-v1040/`
  - 真实运行产物。
- `e/1040/图片/v1040-receipt-check.png`
  - Playwright MCP 截图证据。

## 核心数据结构

v1040 输出包含：

```text
original_summary
rebuilt_summary
original_receipt
rebuilt_receipt
check_rows
summary
```

`original_*` 来自归档的 v1039 receipt。

`rebuilt_*` 来自重新读取 v1038 review 后调用 v1039 builder 的结果。

`check_rows` 是 contract check 的审计表。本版共有 46 条通过检查，包括：

- 顶层 `status`；
- 顶层 `decision`；
- 顶层 `failed_count`；
- `receipt_index_review_sha256`；
- `consumer_receipts`；
- summary 里的 receipt status、consumer、granted use、lookup key count、promotion flag、next step；
- receipt 里的 source paths、review id/status、consumer boundary、model quality claim。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1040(...)` 是主入口。

它执行以下流程：

1. 读取原始 v1039 receipt 的 `summary` 和 `receipt`。
2. 调用 `_resolve_source_review_path(...)` 找到 v1038 source review。
3. 调用 `_rebuild_receipt(...)`，用 v1038 review 重新构建 v1039 receipt。
4. 调用 `_checks(...)` 比较顶层字段、summary 字段、receipt 字段和 consumer receipt rows。
5. 生成 `summary` 和 `interpretation`，暴露 contract check 是否 ready。

`_field_checks(...)` 将字段比较集中成一组表格行，避免每个字段手写重复断言。这也是本版的轻量重构收益：检查范围扩大到 46 项，但代码仍然保持可读。

## CLI 流程

真实运行命令：

```text
python scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1040.py e/1039/解释/receipt-v1039 --out-dir e/1040/解释/receipt-check-v1040 --require-pass --force
```

真实输出摘要：

```text
status=pass
contract_check_ready=True
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

`--require-pass` 使 CLI 在 contract check 失败时返回非零状态。测试中通过篡改 `granted_use` 验证了该失败路径。

## 测试覆盖

focused test 覆盖 6 个路径：

- rebuildable receipt 通过；
- summary/receipt 的 granted use 被篡改会失败；
- source review path 缺失会失败；
- source review digest 被篡改会失败；
- CLI `--require-pass` 对失败 check 返回 `1`；
- JSON/CSV/Text/Markdown/HTML 输出和目录输入都正常。

这些测试保护的是 contract check 的复核价值：v1039 receipt 不能被静默改写成 production use，也不能丢掉 source review。

## 运行证据

运行证据位于：

```text
e/1040/解释/receipt-check-v1040/
e/1040/图片/v1040-receipt-check.png
```

Playwright MCP 快照确认页面展示：

- `Status=pass`；
- `Contract=True`；
- `Failed=0`；
- original/rebuilt use 一致；
- original/rebuilt promotion 一致；
- source review 指向 v1038。

## 一句话总结

v1040 证明 v1039 lookup-only receipt 可以从 v1038 review 重建出来，使下游索引前的收据契约有了可复核保障。

# v1076 publication receipt contract-check 代码讲解

## 本版目标和边界

v1076 的目标是检查 v1075 receipt 是否能从源 v1074 receipt-index review 重新推导出来。它不是新治理链，而是对上一版消费凭证做反向复核：如果 v1075 的 JSON 被手动篡改、源 review 路径丢失、consumer receipt 改变、granted use 被放宽，或者 promotion 字段被误打开，本版都应该失败。

本版不做训练，不改变模型，也不把 contract check 解释为生产批准。它只证明“记录过的 receipt 与源 review 一致”。

## 前置链路

- v1073 产出 digest-backed receipt index。
- v1074 复核 v1073 index，确认只能用于 lookup-only receipt recording。
- v1075 记录 v1074 review 的下游 receipt。
- v1076 重新从 v1074 review build v1075 receipt，并和真实 v1075 receipt 做字段级比对。

这条链路的角色很清楚：v1075 是记录，v1076 是复核。

## 关键文件

### `src/minigpt/...receipt_check_v1076.py`

核心入口是 `build_...receipt_check_v1076()`。它读取 v1075 receipt report，取出：

- `original_summary`
- `original_receipt`
- `receipt_index_review_path`

然后通过 `_resolve_source_review_path()` 找到源 v1074 review，再用 `_rebuild_receipt()` 调用 v1075 的 builder 重建一份 receipt。

比对范围包括：

- 顶层 `status`
- 顶层 `decision`
- 顶层 `failed_count`
- `receipt_index_review_sha256`
- `consumer_receipts`
- summary 字段列表
- receipt 字段列表

字段列表不是随手挑的。`SUMMARY_FIELDS` 保护摘要层对外契约，`RECEIPT_FIELDS` 保护 receipt 主体。两个列表一起覆盖 consumer、use、source paths、lookup keys、quality claim、promotion boundary 和 next step。

### `_resolve_source_review_path()`

这个函数负责从 report 或 receipt body 里找源 review 路径。它支持：

- 绝对路径。
- 当前工作区能直接找到的相对路径。
- 基于 receipt 文件所在目录补全的相对路径。

这样 CLI 既能读真实 `e/1075` 输出，也能在测试临时目录里工作。

### `_rebuild_receipt()`

这个函数是 contract check 的核心。它重新读取 v1074 review JSON，然后调用 v1075 builder：

```python
build_...receipt_v1075(read_json_report(source_review), receipt_index_review_path=source_review)
```

如果源 review 缺失，它返回空对象，后续检查会失败。也就是说，v1076 不信任 v1075 receipt 自己写的结论，而是回到源 review 重新推导。

### `src/minigpt/...receipt_check_v1076_artifacts.py`

artifact writer 输出 JSON、CSV、TXT、Markdown 和 HTML：

- JSON 是后续 index 能消费的结构化证据。
- CSV 展开每个 check row，便于快速定位失败字段。
- TXT 是 CLI 摘要。
- Markdown/HTML 是人工复核证据。

HTML 的关键卡片包括 `Status`、`Contract`、`Original use`、`Rebuilt use`、`Lookup keys`、`Failed`。这能直接看出原始和重建结果是否一致。

### `scripts/...receipt_v1076.py`

CLI 接收 v1075 receipt JSON 或输出目录：

```powershell
python -B scripts\check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1076.py e\1075\解释\receipt-v1075 --out-dir e\1076\解释\receipt-check-v1076 --require-pass --force
```

`--require-pass` 让失败 check 返回非零退出码，适合 CI 或发布前 gate。

## 测试覆盖

测试覆盖六类场景：

- 可重建 receipt 通过。
- granted use 被篡改为 production promotion 时失败。
- 源 review 路径缺失时失败。
- 源 review digest 被篡改时失败。
- CLI 在 `--require-pass` 下对坏 receipt 返回 `1`。
- artifact writer 和 CLI 输出 JSON/CSV/TXT/Markdown/HTML。

本版测试修正了旧模板中的一个语义偏差：v1076 的源 v1074 review 是 ready，所以 v1075 receipt 应该是 lookup-receipted，而不是 blocked。这个修正让测试和真实链路对齐。

## 运行证据

真实 CLI 结果：

- `status=pass`
- `contract_check_ready=True`
- `original_granted_use=downstream_governance_lookup_only`
- `rebuilt_granted_use=downstream_governance_lookup_only`
- `original_lookup_key_count=1`
- `rebuilt_lookup_key_count=1`
- `original_promotion_ready=False`
- `rebuilt_promotion_ready=False`
- `passed_check_count=46`
- `failed_check_count=0`

Playwright MCP snapshot 确认 HTML 页面显示 `Status pass`、`Contract True`、original/rebuilt use 一致、`Failed 0`，并展示源 v1074 review 路径。

## 验证

- focused v1076 tests：`6 passed in 0.32s`
- full pytest：`2771 passed in 537.09s`
- source hygiene：`2166/2166 clean`
- py_compile：新增 Python 文件全部通过。

## 一句话总结

v1076 把 v1075 receipt 从“已记录”推进到“可从源 review 重建且合约稳定”，为下一步 digest-backed index 做准备。

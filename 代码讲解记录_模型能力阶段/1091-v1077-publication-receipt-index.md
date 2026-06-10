# v1077 publication receipt index 代码讲解

## 本版目标和边界

v1077 的目标是把 v1075 lookup-only receipt 与 v1076 contract check 打包成一份新的 receipt index。它不是新治理链，而是把“下游消费凭证”和“凭证可重建验证结果”放进同一个可检索入口里，方便后续 review 或归档模块只读消费。

本版不训练模型，不生成新 checkpoint，不证明模型能力变强，也不允许 promotion。所有关键输出都继续保留 `downstream_governance_lookup_only`、`promotion_ready=False` 和 `bounded_randomized_target_hidden_holdout_claim_only`。

## 前置链路

- v1073 产出 digest-backed receipt index。
- v1074 复核 v1073 index，只允许进入 lookup-only receipt recording。
- v1075 把 v1074 review 记录成 downstream lookup-only receipt。
- v1076 从 v1074 review 重建 v1075 receipt，并确认原始和重建结果一致。
- v1077 消费 v1075 receipt 与 v1076 check，生成新的 receipt index。

这条链路的意义是把“记录”和“复核”合在同一个 lookup entry 里，但不把它升级为生产发布凭证。

## 关键文件

### `src/minigpt/...v1077.py`

核心入口是 `build_...v1077()`。它读取两份结构化报告：

- `receipt_report`：来自 v1075。
- `receipt_check_report`：来自 v1076。

函数先取出 `receipt_summary`、`receipt` 和 `check_summary`，再调用 `_checks()` 生成字段级检查。只要任意检查失败，顶层 `status` 就会变成 `fail`，`receipt_index_rows` 也不会成为可用索引。

主要检查包括：

- receipt 和 check 文件是否存在。
- v1075 receipt 是否 `status=pass` 且 decision ready。
- v1076 contract check 是否 `contract_check_ready=True`。
- receipt status 是否和 v1076 的 original/rebuilt status 一致。
- granted use 是否始终是 `downstream_governance_lookup_only`。
- lookup key 数量是否仍为 1。
- v1075 保留的上游 review/index/receipt/check 路径是否仍然存在。
- consumer boundary 与 model quality claim 是否保持保守。
- `promotion_ready` 和 `approved_for_promotion` 是否仍为 false。
- v1075 的 next step 是否指向 v1076 check，v1076 的 next step 是否指向 v1077 index。

### `_index()`

`_index()` 只在所有检查通过时生成一条 index row。row 里包含：

- `receipt_index_id`
- `lookup_key`
- `receipt_id`
- `receipt_status`
- `granted_use`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_path`
- `contract_check_ready`
- `promotion_ready`

同时它会为 v1075 receipt 与 v1076 check 写两条 `source_evidence_rows`，每条都带 `sha256`。这让后续模块可以判断源文件是否被替换或丢失。

### `resolve_exit_code()`

CLI 的 `--require-index-ready`、`--require-lookup-ready` 和 `--require-promotion-ready` 都走这个函数。v1077 真实运行时要求 index 和 lookup ready，但不会要求 promotion ready，因为这条链路的边界就是只读治理查找。

### `src/minigpt/...v1077_artifacts.py`

artifact writer 输出 JSON、CSV、TXT、Markdown 和 HTML：

- JSON 是后续 review 模块可以消费的结构化证据。
- CSV 展开 `check_rows`，便于定位失败项。
- TXT 给命令行快速读取关键字段。
- Markdown/HTML 给人工复核，页面卡片突出 `Status`、`Index ready`、`Lookup keys`、`Contract`、`Evidence`、`Failed`。

### `scripts/build_...v1077.py`

CLI 支持传入 JSON 文件或输出目录：

```powershell
python -B scripts\build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1077.py --receipt e\1075\解释\receipt-v1075 --receipt-check e\1076\解释\receipt-check-v1076 --out-dir e\1077\解释\receipt-index-v1077 --require-index-ready --require-lookup-ready --force
```

这条命令产出的 `e/1077/解释/receipt-index-v1077/` 是本版最终运行证据，不是临时文件。

## 测试覆盖

`tests/test_...v1077.py` 覆盖四类场景：

- ready receipt + ready contract check 可以生成 pass index。
- 如果 granted use 被改成 production promotion，index 失败。
- 如果 contract check 不 ready，index 失败。
- artifact writer 和 CLI 能输出 JSON/CSV/TXT/Markdown/HTML，并能从目录定位 source JSON。

本版测试还补了一层工程基础设施：新增 `tests/__init__.py`。全量 pytest 曾暴露 188 个 collection import error，原因是多个测试文件复用 `from tests...` helper，而没有显式本地包时会被外部同名 `tests` 包抢占。加入该文件后，全量测试恢复稳定。

## 运行证据

真实 CLI 结果：

- `status=pass`
- `decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1077_ready`
- `index_ready=True`
- `lookup_scope=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP snapshot 确认 HTML 页面显示 `Status pass`、`Index ready True`、`Lookup keys 1`、`Contract True`、`Evidence 2`、`Failed 0`，并能看到 source receipt 与 source check 路径。

## 验证

- focused v1077 tests：`4 passed in 0.41s`
- full pytest：`2775 passed in 520.69s`
- source hygiene：`2171/2171 clean`
- py_compile：新增 Python 文件全部通过。

## 一句话总结

v1077 把 v1075 receipt 和 v1076 contract check 推进成可检索、带 digest、仍严格 lookup-only 的 receipt index，并顺手补稳了全量测试的本地包边界。

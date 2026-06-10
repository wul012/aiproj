# v1075 publication receipt 代码讲解

## 本版目标和边界

v1075 的目标是把 v1074 的 receipt-index review 记录成一个下游 lookup-only receipt。v1074 已经完成对 v1073 receipt index 的只读复核，本版把这个复核结果转化为可被后续 contract check 消费的凭证：谁消费、消费用途是什么、源 review/index/receipt/check 是否仍可追溯，以及 promotion 是否仍被阻断。

本版不新增训练、不改变模型参数、不宣称模型质量提升，也不把 receipt 解释成生产发布批准。它只在治理链里补一个“消费凭证”节点。

## 前置路线

本版延续 v1071-v1074 的四步节奏：

- v1071：记录 v1070 review 的 receipt。
- v1072：重建并检查 v1071 receipt contract。
- v1073：把 v1071 receipt 与 v1072 check 建成 digest-backed index。
- v1074：复核 v1073 index 是否可用于 lookup-only receipt recording。
- v1075：把 v1074 review 记录成新的 receipt，供下一版 contract check 使用。

这里的重点不是“链条越长越好”，而是每个节点都明确保留边界：lookup-only、bounded model-quality claim、no promotion。

## 关键文件

### `src/minigpt/...receipt_v1075.py`

这是 v1075 的核心 builder。入口函数接收 v1074 review report 和可选的 `receipt_index_review_path`，输出统一 receipt report。

核心输入字段包括：

- `summary`：v1074 review 的聚合摘要。
- `review`：v1074 review 的主体，包括 review id、review status、lookup keys 和源路径。
- `receipt_index_rows`：v1073 index 中的 lookup row。
- `source_evidence_rows`：v1071 receipt 和 v1072 check 的 digest-backed source evidence。

核心输出字段包括：

- `status` / `decision`：本版 receipt 是否通过。
- `receipt_index_review_sha256`：源 v1074 review 的文件 digest。
- `consumer_receipts`：下游消费者拿到的 lookup-only 凭证。
- `check_rows`：25 项保护性检查。
- `receipt`：最终可消费的 receipt 主体。
- `summary`：面向 README、HTML 和后续脚本的压缩摘要。

`_checks()` 是主要保护点，覆盖：

- 源 review 文件存在。
- 源 review `status=pass` 且 decision ready。
- `review_status` 只允许 lookup-only receipt recording。
- `requested_use` 必须是 `downstream_governance_lookup_only`。
- lookup ready、contract check ready 必须为 true。
- source evidence 必须有两个、digest 必须存在、状态必须 pass。
- v1073 index row 不允许 promotion。
- model quality claim 保持 `bounded_randomized_target_hidden_holdout_claim_only`。
- 源 review/index/receipt/check 路径必须仍存在。
- 源 next-step 必须匹配 v1074 review 的 record route。

这些检查的意义是：即使有人手动改了 review JSON、改了路径、改了用途、或者误把 promotion 打开，v1075 都会失败。

### `src/minigpt/...receipt_v1075_artifacts.py`

这个文件负责把 builder 的 report 写成 JSON、CSV、TXT、Markdown 和 HTML。

- JSON 是后续 contract check 的主输入。
- CSV 只导出 consumer receipt 行，方便快速核对 consumer、lookup key 和 granted use。
- TXT 是 CLI 摘要。
- Markdown/HTML 是人读证据。

HTML 页面显示 `Status`、`Receipt ready`、`Lookup keys`、`Evidence`、`Use`、`Failed`，并展开源 review/index/receipt/check 的路径边界。

### `scripts/...receipt_v1075.py`

CLI 支持传入 v1074 review JSON 或输出目录：

```powershell
python -B scripts\record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1075.py e\1074\解释\receipt-index-review-v1074 --out-dir e\1075\解释\receipt-v1075 --require-receipt-ready --force
```

`--require-receipt-ready` 会让失败报告返回非零退出码，适合 CI 或手工 gate 使用。`--force` 只用于覆盖本版输出目录，不影响源证据。

### `tests/...receipt_v1075.py`

测试覆盖六个场景：

- ready review 能生成 pass receipt。
- requested use 被改成 production promotion 时失败。
- source review path 漂移时失败。
- source evidence status 改成 fail 时失败。
- CLI 在 `--require-receipt-ready` 下会对坏 review 返回 `1`。
- artifact writer 和 CLI 输出路径完整，文本/Markdown/HTML 都能写出关键内容。

这些测试不是只测函数返回，而是通过 v1074 helper 构造真实上游链路，再写出 review 文件，因此能覆盖路径、JSON、CLI 和 artifact writer 的组合行为。

### 文档和证据

- `e/1075/解释/receipt-v1075/` 保存本版 JSON/CSV/TXT/Markdown/HTML。
- `e/1075/图片/v1075-receipt.png` 是 Playwright MCP 运行截图。
- `e/1075/解释/说明.md` 记录运行命令、关键字段和验证结果。
- `README.md`、`e/README.md`、`代码讲解记录_模型能力阶段/README.md` 更新索引。

## 运行证据

真实 CLI 结果：

- `status=pass`
- `receipt_ready=True`
- `receipt_index_row_count=1`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP snapshot 确认 HTML 页面可见 `Status pass`、`Receipt ready True`、`Failed 0`，并展示 v1074 review、v1073 index、v1071 receipt、v1072 check 的路径。

## 验证

- focused v1075 tests：`6 passed in 1.06s`
- v1075 + source encoding focused tests：`12 passed in 1.38s`
- full pytest：`2765 passed in 754.12s`
- source hygiene：`2162/2162 clean`

验证中发现并修复了 4 个新增 Python 文件的 UTF-8 BOM 问题；修复后 source hygiene 和 full pytest 均通过。

## 一句话总结

v1075 把 v1074 review 从“已复核的只读证据”推进成“可被后续 contract check 消费的 lookup-only receipt”，同时继续保持模型质量声明有界、promotion 不放行。

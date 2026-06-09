# v1042 publication receipt index review 代码讲解

## 本版目标和边界

v1042 的目标是 review v1041 生成的 digest-backed receipt index，判断它是否可以作为下一步 downstream lookup-only receipt 的输入。

它解决的问题是：v1041 已经把 v1039 receipt 与 v1040 contract check 合成索引，但还需要一个只读 review 层确认索引未漂移、源证据仍存在、lookup-only 边界没有变宽。

本版明确不做三件事：

- 不训练或微调模型。
- 不扩大模型质量声明。
- 不把 `promotion_ready` 或 `approved_for_promotion` 置为真。

## 前置链路

本版接在 v1039-v1041 之后：

- v1039：把 v1038 review 后的 receipt index 记录成 downstream lookup-only receipt。
- v1040：从 v1038 review 重新构建 v1039 receipt，做 contract check。
- v1041：把 v1039 receipt 和 v1040 contract check 合成 digest-backed receipt index。
- v1042：review v1041 receipt index，决定是否可以进入下一步 receipt 记录。

因此 v1042 的核心角色不是创建新事实，而是检查 v1041 是否仍然可被 downstream governance lookup 消费。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1042.py`
  - v1042 的核心 review builder。
  - 读取 v1041 index report，抽取 `summary`、`receipt_index`、`receipt_index_rows`、`source_evidence_rows`。
  - 生成 `check_rows`、`review`、`summary`、`interpretation`。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1042_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 用于 Playwright 运行截图，CSV 用于逐项 check 审计。

- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1042.py`
  - CLI 入口。
  - 支持输入 v1041 JSON 文件或输出目录。
  - 支持 `--require-review-ready` 和 `--require-lookup-ready` 作为本地/CI gate。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1042.py`
  - 聚焦测试。
  - 覆盖 ready path、granted use 漂移、source digest 缺失、source path 漂移、CLI/output wiring。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1042 next-step 常量。
  - 把 v1042 review 通过后的路由固定到下一步 receipt 记录。

## 核心数据结构

v1042 report 的主要字段：

- `status`：整体检查结果，只有所有 check 通过才是 `pass`。
- `decision`：稳定决策字符串，pass 时为 `...review_v1042_ready`。
- `failed_count`：失败 check 数。
- `receipt_index_path`：被 review 的 v1041 source index 路径。
- `source_receipt_index_summary`：v1041 summary 的只读拷贝。
- `source_receipt_index`：v1041 receipt_index 的只读拷贝。
- `receipt_index_rows`：通过时保留的 lookup rows；失败时清空，避免下游误消费。
- `source_evidence_rows`：通过时保留两个 source evidence digest rows。
- `check_rows`：22 条检查项。
- `review`：供下游 receipt 记录消费的 review 摘要。
- `summary`：CLI 和 README 可以快速引用的精简状态。
- `interpretation`：解释本版为什么仍然只是 lookup-only。

## 关键函数

`locate_receipt_index_v1042(path)`：

- 如果传入目录，自动拼上 v1041 JSON 文件名。
- 如果传入文件，直接使用该文件。
- 这样 CLI 可以接受 `e/1041/解释/receipt-index-v1041`，也可以接受具体 JSON。

`build_randomized_holdout_publication_..._review_v1042(...)`：

- 是本版核心 builder。
- 先调用 `as_dict` 和 `list_of_dicts` 规范化输入。
- 再由 `_checks` 生成 22 条 contract check。
- 如果有失败项，`status=fail`，并阻断 rows 输出。
- 如果全通过，生成 review-ready 摘要和 next-step。

`_checks(...)`：

它保护的关键边界包括：

- v1041 source index 文件仍存在。
- source index `status=pass`。
- source index decision 必须是 v1041 ready。
- `lookup_scope` 和 `granted_use` 必须仍是 downstream governance lookup only。
- `lookup_ready=True`、`contract_check_ready=True`。
- lookup row 数必须为 1。
- source evidence 必须为 2 条且都有 SHA-256。
- source receipt、receipt check、review、origin receipt index 路径仍存在。
- consumer boundary 和 model quality claim 不能变宽。
- `promotion_ready` 和 `approved_for_promotion` 必须为 false。
- v1041 next-step 必须路由到 review。

`resolve_exit_code(...)`：

- 让 CLI 可以在 `--require-review-ready` 或 `--require-lookup-ready` 下返回非 0。
- `--require-promotion-ready` 仍会失败，因为本链路不允许 promotion。

## 输入输出流程

1. CLI 读取 v1041 JSON。
2. builder 规范化 summary/index/rows/evidence。
3. `_checks` 对 source readiness、路径、digest、lookup-only 边界、promotion 禁止项逐项检查。
4. pass 时生成 `review_ready=True` 的 review 摘要。
5. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
6. Playwright MCP 打开 HTML，归档截图。

## 测试覆盖

聚焦测试覆盖了五类风险：

- ready v1041 index 能通过 review。
- `granted_use` 被篡改为 production promotion 时失败。
- source evidence digest 缺失时失败。
- source receipt path 漂移时失败。
- artifact writer 和 CLI 能真实生成 JSON/CSV/TXT/Markdown/HTML。

这些测试不只是检查函数返回值，还验证 output 文件名、CLI 参数、文本/Markdown/HTML 渲染里关键区块都存在。

## 运行证据

运行证据归档在：

- `e/1042/解释/receipt-index-review-v1042`
- `e/1042/图片/v1042-receipt-index-review.png`

真实 CLI 输出确认：

```text
status=pass
review_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=22
failed_check_count=0
```

Playwright 截图验证 HTML 页面可打开，并能看到 `Review Summary`、`Receipt Index Rows`、`Source Evidence` 和 `Checks`。

## 一句话总结

v1042 把 v1041 receipt index 从 digest-backed lookup evidence 推进为已 review 的 lookup-only 输入，但仍然坚决不把它解释成生产推广或更大模型能力声明。

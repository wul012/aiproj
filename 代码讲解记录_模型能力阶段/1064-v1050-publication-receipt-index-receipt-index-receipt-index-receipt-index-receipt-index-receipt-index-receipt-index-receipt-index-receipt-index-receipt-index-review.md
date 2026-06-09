# v1050 publication receipt index review 代码讲解

## 本版目标和边界

v1050 的目标是 review v1049 digest-backed receipt index，确认它只能进入 downstream lookup-only receipt recording。

它解决的问题是：v1049 已经把 v1047 receipt 和 v1048 contract check 合成索引，但下一步 receipt 不应该直接相信 index ready。v1050 独立检查 index ready、lookup scope、source evidence digest、source path、contract-ready、bounded model-quality claim 和 no-promotion 字段。

本版不做：

- 不训练模型。
- 不新增模型能力评测。
- 不修改 v1049 index。
- 不批准 production promotion。
- 不把 review pass 解释为模型质量提升。

## 前置链路

v1050 直接承接：

- v1047：记录 lookup-only receipt。
- v1048：contract-check v1047 receipt。
- v1049：把 v1047/v1048 写入 digest-backed index。
- v1050：review v1049 index，确认下一步只允许 lookup-only receipt recording。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1050.py`
  - v1050 review builder。
  - 检查 v1049 index report、summary、receipt_index、receipt_index_rows 和 source_evidence_rows。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1050_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 review summary、index rows、source evidence 和 check rows。

- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1050.py`
  - CLI 入口。
  - 支持输入 v1049 index JSON 或目录，支持 `--require-review-ready`、`--require-lookup-ready`、`--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1050.py`
  - 覆盖 ready review、granted use 篡改、source digest 缺失、source path 漂移和 CLI/artifact wiring。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1050 review next-step 常量，指向 v1050 receipt recording。

## 核心数据结构

v1050 输出的核心结构是 `review`：

- `review_ready`
  - 所有 check 通过时为 true。

- `review_status`
  - 固定表达 lookup-only approval，不表达 promotion approval。

- `receipt_index_path`
  - 指向被 review 的 v1049 index JSON。

- `receipt_index_row_count`
  - 期望为 1，确保后续 receipt 只消费一个 lookup row。

- `lookup_keys`
  - 继承 v1049 index 的 lookup key。

- `source_evidence_count`
  - 期望为 2，对应 v1047 receipt 和 v1048 check。

- `source_receipt_path` / `source_receipt_check_path` / `source_review_path` / `source_receipt_index_path`
  - 保留向前追溯路径，便于后续 receipt 解释自己消费了哪些证据。

- `next_step`
  - ready 时进入 v1050 receipt recording。

## 检查项说明

`_checks` 保护 22 个关键条件：

- v1049 index file 必须存在。
- v1049 index status/decision/ready key 必须符合 contract。
- lookup scope 和 granted use 必须保持 downstream lookup-only。
- `lookup_ready=True` 且 `contract_check_ready=True`。
- receipt index rows 必须存在且数量为 1。
- lookup key 必须使用 v1049 receipt-index namespace。
- source evidence 必须有 2 行，且 digest 与 status 都存在并 pass。
- source receipt、source receipt check、source review、source receipt index 路径都必须存在。
- consumer boundary 与 model quality claim 必须保持 governance lookup-only / bounded claim。
- promotion 与 approved-for-promotion 必须保持 false。
- v1049 next_step 必须指向 v1050 review。

## 输入输出流程

CLI 流程：

1. `locate_receipt_index_v1050` 接受 v1049 JSON 或输出目录。
2. `read_json_report` 读取 v1049 index。
3. builder 从 summary/body/rows/evidence 中抽取 review 输入。
4. `_checks` 检查路径、digest、lookup-only 和 no-promotion 字段。
5. `_review` 写出 review summary。
6. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
7. `--require-review-ready` 和 `--require-lookup-ready` 下，不满足条件返回非 0。

## 测试覆盖

聚焦测试验证：

- ready v1049 index 可以通过 review。
- summary 的 `granted_use` 被改成 production promotion 会失败。
- source evidence digest 缺失会失败。
- source receipt path 漂移会失败。
- CLI 可以从目录定位 v1049 JSON，并写出完整五类 artifact。

## 运行证据

运行证据归档在：

- `e/1050/解释/receipt-index-review-v1050`
- `e/1050/图片/v1050-receipt-index-review.png`
- `e/1050/解释/说明.md`

真实 CLI 输出确认：

- `status=pass`
- `review_ready=True`
- `receipt_index_row_count=1`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=22`
- `failed_check_count=0`

Playwright MCP 快照确认 HTML 页面中 `Status=pass`、`Review ready=True`、`Rows=1`、`Lookup keys=1`、`Evidence=2`、`Failed=0` 和 v1047/v1048/v1049 source paths 可见。

本地收口验证：

- focused v1050 tests: `5 passed in 0.44s`
- full pytest: `2633 passed in 526.49s`
- source hygiene: `2062/2062 clean`
- py_compile: pass

## 一句话总结

v1050 把 v1049 index 从“可查”推进到“reviewed and receipt-ready”，但仍明确停在 lookup-only 治理证据边界内。

# v1049 publication receipt index 代码讲解

## 本版目标和边界

v1049 的目标是把 v1047 downstream lookup-only receipt 和 v1048 receipt contract check 写入一个 digest-backed receipt index。

它解决的问题是：v1047 证明“receipt 已记录”，v1048 证明“receipt 可重建且字段未漂移”，但后续 review 不应直接散读两个目录。v1049 提供一个稳定索引，把 receipt、contract check、source evidence digest、lookup key 和 no-promotion 状态放在同一个 report 里。

本版不做：

- 不训练模型。
- 不新增 benchmark。
- 不修改 v1047 receipt 或 v1048 contract check。
- 不批准 production promotion。
- 不把 index ready 解释为模型质量提升。

## 前置链路

v1049 直接承接：

- v1047：记录 v1046 review 的 downstream lookup-only receipt。
- v1048：从 v1046 review 重建并 contract-check v1047 receipt。
- v1049：把 v1047 receipt 和 v1048 check 写入 digest-backed lookup index。

这条链路仍然属于模型能力阶段里的治理证据，不代表模型本体能力提升。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1049.py`
  - v1049 index builder。
  - 读取 receipt summary/body 和 check summary，生成 checks、receipt_index、source_evidence_rows 和 summary。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1049_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 index stats、receipt index rows、source evidence 和 check rows。

- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1049.py`
  - CLI 入口。
  - 支持 `--receipt`、`--receipt-check`、`--out-dir`、`--require-index-ready`、`--require-lookup-ready`、`--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1049.py`
  - 覆盖 ready receipt/check、granted use 篡改、contract check not ready、CLI 和 artifact wiring。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1049 next-step 常量，指向 v1049 review。

## 核心数据结构

v1049 输出的核心结构是 `receipt_index`：

- `index_ready`
  - 只有所有 check 通过时为 true。

- `receipt_index_id`
  - 本版索引 ID，用于报告和 lookup rows。

- `lookup_scope`
  - 固定为 `downstream_governance_lookup_only`。

- `receipt_index_rows`
  - 存放一个 lookup row。
  - row 内包含 lookup key、receipt id/status、granted use、source receipt path、source receipt check path、contract check ready 和 promotion ready。

- `source_evidence_rows`
  - 记录 v1047 receipt JSON 和 v1048 check JSON。
  - 每行包含 kind、path、SHA-256 和 status。

- `next_step`
  - ready 时进入 `review_randomized_holdout_publication_..._v1049`。
  - fail 时进入 repair 路径。

## 检查项说明

`_checks` 保护 25 个关键条件：

- v1047 receipt file 和 v1048 check file 必须存在。
- receipt status/decision/ready key 必须符合 v1047 contract。
- v1048 check 必须 pass，且 `contract_check_ready=True`。
- receipt status、granted use、lookup key count 必须与 contract check 的 original/rebuilt 摘要一致。
- source evidence count 必须为 2。
- receipt 内记录的 v1046 review、v1045 index、v1043 receipt、v1044 check、v1042 review、v1041 origin index 仍然存在。
- consumer boundary 和 model quality claim 必须保持 governance lookup-only / bounded claim。
- promotion 与 approved-for-promotion 必须保持 false。
- v1047/v1048 的 next_step 必须形成 check -> index 的链路。

## 输入输出流程

CLI 流程：

1. `locate_receipt_v1049` 接受 v1047 JSON 或输出目录。
2. `locate_receipt_check_v1049` 接受 v1048 check JSON 或输出目录。
3. `read_json_report` 读取两个 JSON。
4. builder 生成 check rows。
5. `_index` 在所有 check 通过时生成 lookup row 和 source evidence digest。
6. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
7. `--require-index-ready` 或 `--require-lookup-ready` 下，不满足条件返回非 0。

## 测试覆盖

聚焦测试验证：

- ready receipt 和 ready contract check 可以生成 pass index。
- receipt 的 `granted_use` 被篡改为 production promotion 会失败。
- v1048 check 的 `contract_check_ready` 改为 false 会失败。
- CLI 可以从目录定位 JSON，并写出完整五类 artifact。
- text/Markdown/HTML renderer 都暴露关键状态，避免只写 JSON 难以人工复核。

## 运行证据

运行证据归档在：

- `e/1049/解释/receipt-index-v1049`
- `e/1049/图片/v1049-receipt-index.png`
- `e/1049/解释/说明.md`

真实 CLI 输出确认：

- `status=pass`
- `index_ready=True`
- `lookup_ready=True`
- `contract_check_ready=True`
- `source_evidence_count=2`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP 快照确认 HTML 页面中 `Status=pass`、`Index ready=True`、`Lookup keys=1`、`Contract=True`、`Evidence=2`、`Failed=0` 以及 v1047/v1048 source evidence digest 可见。

本地收口验证：

- focused v1049 tests: `4 passed in 0.31s`
- full pytest: `2628 passed in 681.71s`
- source hygiene: `2058/2058 clean`
- py_compile: pass

## 一句话总结

v1049 把 v1047 receipt 和 v1048 contract check 从两个独立证据推进为一个可查、带 digest、仍禁止 promotion 的 receipt index。

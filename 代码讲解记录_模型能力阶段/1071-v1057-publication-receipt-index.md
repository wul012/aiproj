# v1057 publication receipt index 代码讲解

## 本版目标与边界

v1057 的目标是把 v1055 downstream lookup-only receipt 和 v1056 contract check 打包成 digest-backed receipt index。

v1055 负责记录 receipt，v1056 负责证明 receipt 可以从 v1054 review 重新构建。v1057 则把这两个源 artifact 固化为索引：一个 lookup key、一条 receipt row、两条 source evidence，并把下一步路由到 review。

本版不训练模型，不做新评测，不改变 receipt 内容，也不批准 production promotion。

## 前置链路

本版承接：

- v1054：review v1053 index，批准 lookup-only receipt recording。
- v1055：记录 v1054-reviewed index 的 downstream lookup-only receipt。
- v1056：重建 v1055 receipt，证明 receipt contract 稳定。
- v1057：把 v1055 receipt 和 v1056 check 写成 digest-backed index。

这是一条索引化链路，作用是让后续 review 可以从一个固定入口读取 receipt 与 check。

## 关键文件

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1057.py`

这是 v1057 核心 builder。它读取 v1055 receipt 和 v1056 contract check，校验两者状态一致、用途一致、lookup key 一致、source paths 仍存在，并生成 receipt index。

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1057_artifacts.py`

这是 artifact 渲染层，输出 JSON、CSV、text、Markdown 和 HTML。JSON 是后续 review 的输入，HTML 是截图证据。

`scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1057.py`

这是 CLI 入口。真实运行时输入 v1055 receipt 目录和 v1056 check 目录，输出 `e/1057/解释/receipt-index-v1057`。

`tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1057.py`

这是 focused 测试，覆盖 ready receipt/check、granted use 越界、contract check 未 ready，以及 CLI/artifact wiring。

`src/minigpt/randomized_holdout_publication_constants.py`

本版新增 v1057 next-step 常量，index ready 后指向 v1057 review。

## 核心数据结构

v1057 report 的核心字段：

- `receipt_path`：v1055 receipt JSON 路径。
- `receipt_check_path`：v1056 contract check JSON 路径。
- `source_receipt_summary`：v1055 receipt summary。
- `source_receipt_check_summary`：v1056 check summary。
- `receipt_index_rows`：索引行，包含 lookup key、receipt id、source receipt/check path、source review path 和 promotion flag。
- `source_evidence_rows`：两条 evidence，分别记录 receipt 和 receipt_check 的路径、SHA-256 与状态。
- `receipt_index`：完整 index 对象。
- `summary`：CLI/HTML 展示摘要。
- `check_rows`：25 项索引前检查。

## 运行流程

1. CLI 定位 v1055 receipt JSON 和 v1056 check JSON。
2. builder 读取两个 report，提取 receipt summary、receipt body 和 check summary。
3. `_checks()` 校验 receipt/check 文件存在、二者 status/pass、receipt decision ready、contract check ready、granted use、lookup key count、source paths、consumer boundary、model quality claim 和 no-promotion。
4. `_index()` 生成 receipt index row 与 source evidence rows。
5. `_summary()` 汇总 index ready、lookup scope、source evidence count、lookup ready、contract check ready 和 next-step。
6. artifact writer 输出 JSON、CSV、text、Markdown、HTML。

## 关键断言

v1057 最关键的保护点：

- `receipt_file_exists` 和 `receipt_check_file_exists`：两个源 artifact 必须存在。
- `receipt_passed` 和 `receipt_check_passed`：源 receipt/check 必须都是 pass。
- `receipt_decision_ready`：v1055 receipt 必须是 ready decision。
- `receipt_check_decision_ready`：v1056 check 必须是 passed decision。
- `receipt_status_matches_check`：receipt 状态要和 contract check 的 original/rebuilt 状态一致。
- `granted_use_lookup_only`：receipt 与 check 中的用途都必须是 lookup-only。
- `lookup_key_count`：lookup key 必须稳定为 1。
- `source_*_file_exists`：v1054/v1053/v1051/v1052/v1050/v1049 源链路仍可追溯。
- `promotion_still_false`：索引不能打开 promotion。
- `source_next_steps_match`：v1055 指向 check，v1056 指向 index。

## 测试覆盖

focused v1057 测试覆盖 4 个场景：

- ready receipt/check 可以生成 index。
- 篡改 `granted_use` 会 fail。
- contract check 未 ready 会 fail。
- CLI 和 artifact writer 能生成完整输出。

真实证据使用 `e/1055` 与 `e/1056` 的归档产物运行。

## 运行证据

真实 CLI 证据在：

- `e/1057/解释/receipt-index-v1057/`

Playwright MCP 截图在：

- `e/1057/图片/v1057-receipt-index.png`

页面显示：

- `Status=pass`
- `Index ready=True`
- `Lookup keys=1`
- `Evidence=2`
- `Scope=downstream_governance_lookup_only`
- `Failed=0`

## 边界说明

v1057 的通过结论只表示 v1055 receipt 与 v1056 check 已经形成 digest-backed lookup index。它不代表模型训练质量提高，不改变 baseline/candidate 结论，不允许 production promotion。

一句话总结：v1057 把 receipt 和 contract check 固化为可查索引，为下一步只读 review 提供稳定、带 digest 的入口。

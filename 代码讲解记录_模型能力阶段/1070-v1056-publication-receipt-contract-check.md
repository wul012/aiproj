# v1056 publication receipt contract check 代码讲解

## 本版目标与边界

v1056 的目标是 contract-check v1055 receipt：从 v1055 receipt 里找到源 v1054 review，重新调用 v1055 receipt builder，确认重建结果和原始 receipt 完全一致。

v1055 已经记录一个 downstream lookup-only consumer receipt。v1056 不创建新 receipt，不改 lookup index，不训练模型，而是检查这个 receipt artifact 是否能从源 review 重新推导出来。这样可以防止 receipt JSON 被手工改写、source path 丢失、granted use 越界、promotion 字段被打开，或者 next-step 被改到错误路线。

本版不批准 production promotion，不扩大模型质量声明，不进入 runtime serving。

## 前置链路

本版承接：

- v1053：把 v1051 receipt 和 v1052 check 写成 digest-backed index。
- v1054：review v1053 index，批准 lookup-only receipt recording。
- v1055：记录 v1054-reviewed index 的 downstream lookup-only receipt。
- v1056：从 v1054 review 重建 v1055 receipt，并比较全部关键字段。

这是一条 receipt 可复建链路，不是新治理链。

## 关键文件

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1056.py`

这是 v1056 核心 builder。它读取 v1055 receipt report，解析 `receipt_index_review_path`，重新构建 v1055 receipt，并输出 contract check report。

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1056_artifacts.py`

这是渲染层，输出 JSON、CSV、text、Markdown 和 HTML。HTML 用于截图，CSV 展开 46 项字段比较，JSON 给后续 index 消费。

`scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1056.py`

这是 CLI 入口。真实运行时输入 `e/1055/解释/receipt-v1055`，输出 `e/1056/解释/receipt-check-v1056`。

`tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1056.py`

这是 focused 测试，覆盖可重建 receipt、granted use 篡改、source review 缺失、source digest 篡改、`--require-pass` 失败返回 1，以及 CLI/artifact wiring。

`src/minigpt/randomized_holdout_publication_constants.py`

本版新增 v1056 next-step 常量，contract check 通过后指向 v1056 index。

## 核心数据结构

v1056 report 的核心字段：

- `receipt_path`：输入的 v1055 receipt JSON 路径。
- `source_receipt_index_review`：从 receipt 里解析出的 v1054 review 路径。
- `original_summary`：原始 v1055 receipt summary。
- `rebuilt_summary`：从 v1054 review 重新构建的 v1055 receipt summary。
- `original_receipt`：原始 v1055 receipt body。
- `rebuilt_receipt`：重建出来的 v1055 receipt body。
- `check_rows`：46 项 contract check rows。
- `summary`：压缩展示 status、source review、original/rebuilt 状态和 next-step。
- `interpretation`：说明通过或失败时的边界。

## 运行流程

1. CLI 定位 v1055 receipt JSON。
2. builder 提取原始 summary 和 receipt。
3. `_resolve_source_review_path()` 从 `receipt_index_review_path` 找到 v1054 review。
4. `_rebuild_receipt()` 调用 v1055 receipt builder，使用同一个 v1054 review 重新生成 receipt。
5. `_checks()` 比较顶层 status、decision、failed_count、source digest、consumer receipts。
6. `_field_checks()` 分别比较 summary 字段和 receipt 字段。
7. artifact writer 输出 JSON、CSV、text、Markdown、HTML。

## 关键断言

v1056 最关键的保护点：

- `source_receipt_index_review_exists`：v1054 review 仍然可定位。
- `status` / `decision` / `failed_count`：原始和重建顶层结论一致。
- `receipt_index_review_sha256`：源 review digest 一致。
- `consumer_receipts`：consumer receipt 没有漂移。
- `summary.granted_use` 和 `receipt.granted_use`：用途仍是 lookup-only。
- `summary.promotion_ready` 和 `receipt.promotion_ready`：promotion 仍然关闭。
- `receipt.source_receipt_index_path`、`receipt.source_receipt_path`、`receipt.source_receipt_check_path`、`receipt.source_review_path`、`receipt.source_receipt_index_origin_path`：源路径保持一致。
- `summary.next_step` 和 `receipt.next_step`：后续路线保持一致。

## 测试覆盖

focused v1056 测试覆盖 6 个场景：

- 可重建 receipt 通过 contract check。
- 篡改 `granted_use` 会 fail。
- source review 缺失会 fail。
- source digest 篡改会 fail。
- `--require-pass` 对失败 check 返回 1。
- CLI 和 artifact writer 能生成完整输出。

真实证据使用 `e/1055` 归档 receipt 运行，证明不是只在测试夹具里通过。

## 运行证据

真实 CLI 证据在：

- `e/1056/解释/receipt-check-v1056/`

Playwright MCP 截图在：

- `e/1056/图片/v1056-receipt-check.png`

页面显示：

- `Status=pass`
- `Contract=True`
- `Original use=downstream_governance_lookup_only`
- `Rebuilt use=downstream_governance_lookup_only`
- `Lookup keys=1`
- `Failed=0`

## 边界说明

v1056 的通过结论只表示 v1055 receipt 能从 v1054 review 复建，且所有关键字段一致。它不表示模型质量提升，不表示 baseline/candidate 选择变化，也不表示 production promotion 可以打开。

一句话总结：v1056 把 v1055 receipt 从“已登记”推进到“可复建且合同稳定”。

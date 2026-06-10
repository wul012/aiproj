# v1065 publication receipt index 代码讲解

## 本版目标与边界

v1065 的目标是把 v1063 receipt 和 v1064 contract check 索引成 digest-backed lookup evidence。

v1065 不重做 receipt，也不重做 contract check，而是把两者组合成一个可供后续 review 的 index report。它保留 source receipt、source receipt check、source evidence digest、lookup-only scope、contract-check ready 和 next-step routing。

本版不训练模型，不做 benchmark，不扩大模型质量声明，不批准 production promotion。

## 前置链路

本版承接：

- v1063：把 v1062 review 记录成 downstream lookup-only receipt。
- v1064：contract-check v1063 receipt，证明它可由 v1062 review 重建。
- v1065：把 v1063 receipt 和 v1064 contract check 索引成 lookup-backed evidence。

这还是治理证据链，不是模型能力提升链。

## 关键文件

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1065.py`

这是 v1065 核心 builder，负责读取 v1063 receipt 和 v1064 contract check，校验两边都 ready，并生成 receipt index 对象。

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1065_artifacts.py`

这是渲染层，输出 JSON、CSV、text、Markdown、HTML。HTML 用于截图，CSV 存 check rows。

`scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1065.py`

这是 CLI 入口。真实运行时输入 `e/1063/解释/receipt-v1063` 和 `e/1064/解释/receipt-check-v1064`，输出 `e/1065/解释/receipt-index-v1065`。

`tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1065.py`

这是 focused 测试，覆盖 ready receipt + check、granted use 篡改、contract check 不 ready、以及 CLI/artifact wiring。

`src/minigpt/randomized_holdout_publication_constants.py`

本版新增 v1065 next-step 常量，index 通过后指向 v1065 review。

## 核心数据结构

v1065 report 的核心字段：

- `receipt_path`：输入的 v1063 receipt JSON 路径。
- `receipt_check_path`：输入的 v1064 contract-check JSON 路径。
- `source_receipt_summary`：v1063 receipt summary。
- `source_receipt_check_summary`：v1064 contract-check summary。
- `receipt_index_rows`：索引出来的 receipt index rows。
- `source_evidence_rows`：receipt 和 contract-check 两条 evidence。
- `receipt_index`：本版 index 对象。
- `summary`：CLI/HTML 使用的压缩摘要。
- `check_rows`：25 项 index checks。

receipt index 对象的关键字段：

- `index_ready`
- `receipt_index_id`
- `lookup_scope`
- `lookup_key_count`
- `receipt_id`
- `receipt_status`
- `granted_use`
- `source_evidence_count`
- `lookup_ready`
- `contract_check_ready`
- `promotion_ready`
- `approved_for_promotion`
- `source_next_step`
- `next_step`

## 运行流程

1. CLI 定位 v1063 receipt 和 v1064 contract-check JSON。
2. builder 读取两份 report，提取 summary、receipt、check_summary。
3. `_checks()` 校验文件存在、receipt pass、decision ready、lookup-only use、contract-check ready、row 数、digest 和 no-promotion。
4. `_index()` 把 receipt 和 check 组合成 lookup-backed index。
5. `_summary()` 汇总 index 状态和下一步。
6. artifact writer 输出 JSON、CSV、text、Markdown、HTML。

## 关键断言

v1065 最关键的保护点：

- `receipt_status_ready`：receipt 必须仍然是 lookup receipted。
- `receipt_check_passed` / `receipt_check_decision_ready`：contract-check 必须通过且 ready。
- `lookup_key_count`：索引必须只保留一个 lookup key。
- `source_evidence_count`：必须保留两条 evidence。
- `source_next_steps_match`：receipt 必须指向 check，check 必须指向 index。
- `promotion_still_false`：index 不允许把 promotion 打开。

## 测试覆盖

focused v1065 测试覆盖 4 个场景：

- ready receipt 和 check 可以生成 index。
- 篡改 `granted_use` 会 fail。
- contract check 不 ready 会 fail。
- CLI 和 artifact writer 能生成完整输出。

真实证据使用 `e/1063` 和 `e/1064` 归档产物运行，不只依赖测试夹具。

## 运行证据

真实 CLI 证据在：

- `e/1065/解释/receipt-index-v1065/`

Playwright MCP 截图在：

- `e/1065/图片/v1065-receipt-index.png`

页面显示：

- `Status=pass`
- `Index ready=True`
- `Lookup keys=1`
- `Evidence=2`
- `Failed=0`

补充验证：

- focused v1065 tests: `4 passed in 0.31s`
- full pytest: `2712 passed in 663.60s`
- source hygiene: `2122/2122 clean`

## 边界说明

v1065 的通过结论只表示 v1063 receipt 和 v1064 contract check 已被索引成 lookup-backed evidence。它不表示模型质量提高，不表示训练成功，也不表示生产推广。

一句话总结：v1065 把 receipt 与 contract-check 汇成可检索索引，让下一轮 review 可以沿着稳定 evidence 继续走。

# v1054 publication receipt index review 代码讲解

## 本版目标与边界

v1054 的目标是 review v1053 digest-backed receipt index，并决定它是否可以进入下一步 receipt recording。

v1053 已经把 v1051 receipt 和 v1052 contract check 写成一个带 SHA-256 的 lookup index。v1054 不再重新打包 index，而是检查 v1053 index 的状态、lookup scope、source evidence、source paths、no-promotion 字段和 next-step 路由，然后输出 review report。

本版不训练模型，不做 benchmark，不扩大模型质量声明，不批准 production promotion。它只允许下一步“记录 lookup-only receipt”。

## 前置链路

本版承接：

- v1051：记录 v1050 reviewed index 的 downstream lookup-only receipt。
- v1052：重建 v1051 receipt，证明 receipt 与 v1050 review 一致。
- v1053：把 v1051 receipt 和 v1052 check 写成 digest-backed index。
- v1054：review v1053 index，并限制它只能用于 lookup-only receipt recording。

这是一条治理证据链，不是模型能力提升链。

## 关键文件

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1054.py`

这是 v1054 核心 builder，负责读取 v1053 index，执行 review checks，并生成 review 对象。

`src/minigpt/..._review_v1054_artifacts.py`

这是渲染层，输出 JSON、CSV、text、Markdown、HTML。CSV 存 check rows，HTML 用于运行截图。

`scripts/review_..._v1054.py`

这是 CLI 入口。真实运行时输入 `e/1053/解释/receipt-index-v1053`，输出 `e/1054/解释/receipt-index-review-v1054`。

`tests/test_..._review_v1054.py`

这是 focused 测试，覆盖 ready index、granted use 篡改、source digest 缺失、source path 漂移，以及 CLI/artifact wiring。

`src/minigpt/randomized_holdout_publication_constants.py`

本版新增 v1054 next-step 常量，review 通过后指向 v1054 receipt recording。

## 核心数据结构

v1054 report 的核心字段：

- `source_receipt_index_summary`：v1053 index 的 summary。
- `source_receipt_index`：v1053 index 的完整 index body。
- `receipt_index_rows`：通过 review 后保留的 index rows。
- `source_evidence_rows`：通过 review 后保留的 receipt/check evidence。
- `review`：本版 review 对象。
- `summary`：面向 CLI/HTML 的压缩摘要。
- `check_rows`：22 项 review checks。

review 对象的关键字段：

- `review_ready`
- `review_id`
- `review_status`
- `receipt_index_path`
- `lookup_keys`
- `source_evidence_count`
- `lookup_ready`
- `contract_check_ready`
- `granted_use`
- `promotion_ready`
- `approved_for_promotion`
- `next_step`

## 运行流程

1. CLI 定位 v1053 index JSON。
2. builder 读取 index report，提取 summary、receipt_index、index rows 和 source evidence rows。
3. `_checks()` 校验 index 文件存在、source index pass、decision ready、lookup-only scope、contract check ready、row 数、digest、source path 和 no-promotion。
4. `_review()` 在所有 check 通过后生成 review 对象。
5. `_summary()` 汇总 review 状态和下一步。
6. artifact writer 输出 JSON/CSV/text/Markdown/HTML。

## 关键断言

v1054 最关键的保护点：

- `receipt_index_decision_ready`：v1053 index 必须是 ready decision。
- `lookup_scope_downstream` / `granted_use_lookup_only`：索引用途不能越界。
- `source_evidence_digests_present`：v1051/v1052 的 SHA-256 不能缺失。
- `source_receipt_file_exists` / `source_receipt_check_file_exists`：源 receipt/check 仍然存在。
- `promotion_still_false`：review 不能把任何字段变成 promotion-ready。
- `source_next_step_matches`：v1053 必须把下一步路由到 review。

## 测试覆盖

focused v1054 测试覆盖 5 个场景：

- ready v1053 index 可以被 review。
- 篡改 `granted_use` 会 fail。
- source evidence digest 缺失会 fail。
- source path 漂移会 fail。
- CLI 和 artifact writer 能生成完整输出。

真实证据使用 `e/1053` 归档产物运行，不只依赖测试夹具。

## 运行证据

真实 CLI 证据在：

- `e/1054/解释/receipt-index-review-v1054/`

Playwright MCP 截图在：

- `e/1054/图片/v1054-receipt-index-review.png`

页面显示：

- `Status=pass`
- `Review ready=True`
- `Rows=1`
- `Lookup keys=1`
- `Evidence=2`
- `Failed=0`

## 边界说明

v1054 的通过结论只表示 v1053 index 可以用于 lookup-only receipt recording。它不表示模型质量提高，不表示训练成功，也不表示生产推广。

一句话总结：v1054 给 v1053 index 增加只读 review 门禁，把下一步限制在 lookup-only receipt recording。

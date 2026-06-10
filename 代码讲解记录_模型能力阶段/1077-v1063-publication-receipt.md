# v1063 publication receipt 代码讲解

## 本版目标与边界

v1063 的目标是把 v1062 review 过的 receipt index 记录成 downstream lookup-only receipt。

v1062 已经确认 v1061 index 可以用于 lookup-only receipt recording。v1063 不重新 review index，也不改变 v1061/v1062 的判断，而是创建 receipt report，记录使用者、授权用途、源 review SHA-256、source paths、consumer receipts 和下一步 contract-check 路由。

本版不训练模型，不做 benchmark，不扩大模型质量声明，不批准 production promotion。

## 前置链路

本版承接：

- v1059：上一轮 lookup-only receipt。
- v1060：检查 v1059 receipt 是否可由 v1058 review 重建。
- v1061：索引 v1059 receipt 与 v1060 check。
- v1062：review v1061 index。
- v1063：把 v1062 review 结果记录为 downstream lookup-only receipt。

这仍然是治理证据链，不是模型能力提升链。

## 关键文件

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1063.py`

这是 v1063 核心 builder，负责读取 v1062 review，校验 review ready、lookup-only use、source paths、source evidence digest、source checks 和 no-promotion 字段，并生成 receipt 对象。

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1063_artifacts.py`

这是渲染层，输出 JSON、CSV、text、Markdown、HTML。HTML 是运行截图的对象，CSV 存 check rows。

`scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1063.py`

这是 CLI 入口。真实运行时输入 `e/1062/解释/receipt-index-review-v1062`，输出 `e/1063/解释/receipt-v1063`。

`tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1063.py`

这是 focused 测试，覆盖 ready review、requested use 篡改、source review path 漂移、source evidence status 漂移、CLI failure exit 和 artifact wiring。

`src/minigpt/randomized_holdout_publication_constants.py`

本版新增 v1063 next-step 常量，receipt 通过后指向 v1063 contract check。

## 核心数据结构

v1063 report 的核心字段：

- `receipt_index_review_path`：输入的 v1062 review JSON 路径。
- `receipt_index_review_sha256`：v1062 review JSON 的 SHA-256。
- `source_receipt_index_review_summary`：v1062 review summary。
- `source_receipt_index_review`：v1062 review body。
- `receipt_index_rows`：被记录的 source index rows。
- `source_evidence_rows`：v1059/v1060 的源 evidence。
- `consumer_receipts`：下游消费 receipt 行。
- `receipt`：本版 receipt 对象。
- `summary`：CLI/HTML 使用的压缩摘要。
- `check_rows`：25 项 receipt checks。

receipt 对象的关键字段：

- `receipt_ready`
- `receipt_id`
- `receipt_status`
- `consumer_name`
- `requested_use`
- `granted_use`
- `receipt_index_review_sha256`
- `lookup_keys`
- `promotion_ready`
- `approved_for_promotion`
- `source_receipt_index_path`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `next_step`

## 运行流程

1. CLI 定位 v1062 review JSON。
2. builder 读取 review report，提取 review summary、review body、index rows 和 source evidence rows。
3. `_checks()` 校验 review 文件存在、review pass、ready decision、lookup-only grant、source evidence、source paths 和 no-promotion。
4. `_receipt()` 生成 downstream lookup-only receipt。
5. `_consumer_receipts()` 生成下游消费行。
6. `_summary()` 汇总 receipt 状态和下一步。
7. artifact writer 输出 JSON、CSV、text、Markdown、HTML。

## 关键断言

v1063 最关键的保护点：

- `receipt_index_review_decision_ready`：v1062 review 必须是 ready decision。
- `requested_use_allowed`：调用方请求用途只能是 downstream lookup-only。
- `lookup_only_granted_use`：review grant 不能越界。
- `source_evidence_digests_present`：源 receipt/check 的 SHA-256 不能缺失。
- `source_review_file_exists` / `source_receipt_index_file_exists` / `source_receipt_check_file_exists`：源路径仍然存在。
- `promotion_still_false`：receipt 不能把任何字段变成 promotion-ready。
- `source_next_step_matches`：v1062 必须把下一步路由到 receipt recording。

## 测试覆盖

focused v1063 测试覆盖 6 个场景：

- ready v1062 review 可以生成 receipt。
- 篡改 requested use 会 fail。
- source review path 漂移会 fail。
- source evidence status 漂移会 fail。
- `--require-receipt-ready` 对失败 report 返回 1。
- CLI 和 artifact writer 能生成完整输出。

真实证据使用 `e/1062` 归档产物运行，不只依赖测试夹具。

## 运行证据

真实 CLI 证据在：

- `e/1063/解释/receipt-v1063/`

Playwright MCP 截图在：

- `e/1063/图片/v1063-receipt.png`

页面显示：

- `Status=pass`
- `Receipt ready=True`
- `Lookup keys=1`
- `Evidence=2`
- `Failed=0`

补充验证：

- focused v1063 tests: `6 passed in 0.52s`
- full pytest: `2702 passed in 679.91s`
- source hygiene: `2114/2114 clean`

## 边界说明

v1063 的通过结论只表示 v1062 review 后的 index 已被记录为 downstream lookup-only receipt。它不表示模型质量提高，不表示训练成功，也不表示生产推广。

一句话总结：v1063 把 v1062 review 结果落成 receipt，为下一步 receipt contract check 提供稳定输入。

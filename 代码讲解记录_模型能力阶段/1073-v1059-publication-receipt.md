# v1059 publication receipt 代码讲解

## 本版目标与边界

v1059 的目标是把 v1058 review 过的 receipt index 登记成 downstream lookup-only receipt。

v1058 已经检查 v1057 index 的 source evidence、lookup scope、contract check ready、source paths 和 no-promotion 字段。v1059 不重新 review index，也不重新计算模型能力，而是记录一个正式消费凭证：哪个 consumer 使用了这个 reviewed index、用途是否仍然是 `downstream_governance_lookup_only`、源 receipt/check/review/index 是否仍然存在、下一步是否进入 contract check。

本版不训练模型，不新增评测，不批准 promotion，不把 receipt 当成模型质量提升证据。它只把治理链路从“review 完成”推进到“receipt 已登记”。

## 前置链路

本版承接：

- v1053：把 v1051 receipt 和 v1052 check 写成 digest-backed receipt index。
- v1054：review v1053 index，批准 lookup-only receipt recording。
- v1055：记录 v1054 reviewed index 的 downstream lookup-only receipt。
- v1056：重建 v1055 receipt，验证 receipt contract 稳定。
- v1057：把 v1055 receipt 和 v1056 check 写成 digest-backed receipt index。
- v1058：review v1057 index，批准 lookup-only receipt recording。
- v1059：记录 v1058 reviewed index 的 downstream lookup-only receipt。

这条链路仍是治理证据链，不是模型训练链。

## 关键文件

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1059.py`

这是 v1059 核心 builder，负责读取 v1058 review report，校验源 review、source evidence、source paths、lookup-only 用途和 next-step，然后生成 receipt report。

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1059_artifacts.py`

这是 artifact 渲染层，输出 JSON、CSV、text、Markdown 和 HTML。JSON 用于后续 contract check 消费，CSV 展开 checks，HTML 用于运行截图。

`scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1059.py`

这是 CLI 入口。真实运行时输入 `e/1058/解释/receipt-index-review-v1058`，输出 `e/1059/解释/receipt-v1059`。

`tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1059.py`

这是 focused 测试，覆盖 ready receipt、granted use 越界、source evidence 缺失、source path 漂移、next-step 漂移，以及 CLI/artifact wiring。

`src/minigpt/randomized_holdout_publication_constants.py`

本版新增 v1059 next-step 常量，receipt ready 后指向 v1059 contract check。

## 核心数据结构

v1059 report 的核心字段：

- `receipt_index_review_path`：输入的 v1058 review JSON 路径。
- `source_receipt_index_review_summary`：v1058 review summary。
- `source_receipt_index_review`：v1058 review body。
- `receipt_index_rows`：v1058 review 保留下来的 v1057 index rows。
- `source_evidence_rows`：v1055 receipt 和 v1056 check 的 digest-backed evidence。
- `consumer_receipts`：本版新增的 lookup-only consumer receipt。
- `receipt`：本版 receipt 对象。
- `summary`：面向 CLI/HTML 的压缩摘要。
- `check_rows`：25 项 receipt checks。

receipt 对象的关键字段：

- `receipt_ready`
- `receipt_id`
- `receipt_status`
- `consumer_name`
- `granted_use`
- `receipt_index_review_path`
- `source_receipt_index_path`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_origin_path`
- `lookup_keys`
- `source_evidence_count`
- `promotion_ready`
- `next_step`

## 运行流程

1. CLI 定位 v1058 review JSON。
2. builder 读取 review report，提取 summary、review、index rows 和 source evidence rows。
3. `_checks()` 校验 review 文件存在、review pass、decision ready、lookup-only use、source evidence digest、source paths、consumer boundary、bounded model-quality claim 和 no-promotion 字段。
4. `_receipt()` 在 checks 全部通过后生成 receipt 对象。
5. `_consumer_receipts()` 写出下游 consumer 的 lookup key、source receipt、source check 和 granted use。
6. `_summary()` 生成 CLI/HTML 摘要。
7. artifact writer 输出 JSON、CSV、text、Markdown、HTML。

## 关键断言

v1059 最关键的保护点：

- `receipt_index_review_passed`：v1058 review 必须是 pass。
- `receipt_index_review_decision_ready`：v1058 review 必须是 ready decision。
- `requested_use_allowed` / `lookup_only_granted_use`：用途必须维持 downstream governance lookup only。
- `source_evidence_digests_present`：v1055/v1056 的 SHA-256 不能缺失。
- `source_receipt_index_file_exists`：v1057 index 仍然存在。
- `source_receipt_file_exists` / `source_receipt_check_file_exists`：v1055 receipt 和 v1056 check 仍然存在。
- `source_review_file_exists` / `source_receipt_index_origin_file_exists`：v1054 review 和 v1053 index 仍然存在。
- `promotion_still_false`：receipt 不能打开 promotion。
- `source_next_step_matches`：v1058 必须把下一步路由到 receipt recording。

## 测试覆盖

focused v1059 测试覆盖 6 个场景：

- ready v1058 review 可以生成 lookup-only receipt。
- 篡改 `granted_use` 会 fail。
- source evidence 缺失会 fail。
- source path 漂移会 fail。
- source next-step 漂移会 fail。
- CLI 和 artifact writer 能生成完整输出。

真实证据使用 `e/1058` 归档产物运行，不只依赖测试夹具。

## 运行证据

真实 CLI 证据在：

- `e/1059/解释/receipt-v1059/`

Playwright MCP 截图在：

- `e/1059/图片/v1059-receipt.png`

页面显示：

- `Status=pass`
- `Receipt ready=True`
- `Lookup keys=1`
- `Evidence=2`
- `Use=downstream_governance_lookup_only`
- `Failed=0`

## 边界说明

v1059 的通过结论只表示 v1058 reviewed index 已被登记为 downstream lookup-only receipt。它不代表模型训练质量提升，不代表 candidate/baseline 有新结论，也不代表可以进入生产推广。

一句话总结：v1059 给 v1058 review 后的 receipt index 留下正式 lookup-only 消费凭证，并把下一步约束到 v1059 contract check。

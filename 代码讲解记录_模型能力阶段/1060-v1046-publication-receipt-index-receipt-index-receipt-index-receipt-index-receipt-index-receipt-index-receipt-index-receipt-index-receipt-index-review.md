# v1046 publication receipt index review 代码讲解

## 本版目标和边界

v1046 的目标是 review v1045 digest-backed receipt index。

它解决的问题是：v1045 已经把 v1043 downstream lookup-only receipt 和 v1044 receipt contract check 写入一个新的 receipt index，但后续如果直接继续记录 receipt，会缺少一层“index 本身是否仍然干净”的批准证据。v1046 就是这层只读 review。

本版不做：

- 不训练模型。
- 不新增 benchmark。
- 不修改 v1045 index 的内容。
- 不把 lookup-ready 解释为生产可用。
- 不开启 production promotion。

## 前置链路

v1046 直接承接：

- v1043：记录 downstream lookup-only consumer receipt。
- v1044：重建并检查 v1043 receipt，确认 original/rebuilt 字段一致。
- v1045：把 v1043 receipt 和 v1044 contract check 写入 digest-backed receipt index。
- v1046：对 v1045 index 做只读 review，确认它可以进入下一步 receipt 记录。

这条链路的重点仍然是治理证据，而不是模型能力提升。它保证 downstream consumer 只能按 lookup-only 边界消费前面已经审过的 tiny 模型能力证据。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1046.py`
  - v1046 review builder。
  - 读取 v1045 index JSON，检查 status、decision、ready key、lookup-only scope/use、source evidence、source path、promotion=false 和 next-step。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1046_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 用于 Playwright MCP 页面检查和截图。

- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1046.py`
  - CLI 入口。
  - 支持输入 v1045 JSON 或输出目录，支持 `--require-review-ready`、`--require-lookup-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1046.py`
  - 覆盖 ready path、granted use 漂移、source evidence digest 缺失、source path 漂移、CLI/output wiring。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1046 next-step 常量，路由到下一步 receipt 记录。

## 核心数据结构

`review` 字段是本版最重要的输出：

- `review_ready`：所有检查通过时为 true。
- `review_id`：稳定 review ID。
- `review_status`：固定为 lookup-only review 状态。
- `receipt_index_path`：被审查的 v1045 index 路径。
- `receipt_index_id`：v1045 index 的稳定 ID。
- `receipt_index_row_count`：当前为 1。
- `lookup_keys`：v1045 提供的 downstream lookup key。
- `source_evidence_count`：当前为 2，对应 receipt 和 receipt check。
- `lookup_ready`：是否允许进入 downstream lookup 消费。
- `contract_check_ready`：v1044 contract check 是否仍被 v1045 index 记录为 ready。
- `promotion_ready=False` 和 `approved_for_promotion=False`：继续明确阻断生产推广。
- `source_receipt_path`、`source_receipt_check_path`、`source_review_path`、`source_receipt_index_path`：保留上游链路路径，方便后续审计。
- `next_step`：通过时路由到 v1046 receipt 记录。

`summary` 字段把这些状态压成 CLI 和 HTML 可以直接展示的摘要：

- ready key
- review status
- receipt index row count
- lookup key count
- source evidence count
- lookup ready
- contract check ready
- granted use
- promotion state
- model quality claim
- next step
- passed/failed check count

## 检查项说明

`_checks` 保护 22 个条件，核心分成六组：

1. 文件与 source 状态
   - v1045 receipt index 文件必须存在。
   - v1045 index 的 `status` 和 `decision` 必须 ready。
   - v1045 summary ready key 和 body `index_ready` 必须同时为 true。

2. lookup-only 边界
   - `lookup_scope` 在 summary 和 body 中都必须是 downstream lookup-only。
   - `granted_use` 在 summary 和 body 中都必须是 downstream lookup-only。
   - lookup key 必须使用 v1045 的 receipt-index namespace。

3. index 内容完整性
   - index row 数量必须等于 summary 中的 `lookup_key_count`，且当前为 1。
   - source evidence 数量必须为 2。
   - source evidence digest 必须存在。
   - source evidence status 必须都是 pass。

4. 上游路径稳定性
   - v1043 receipt 路径仍存在。
   - v1044 receipt check 路径仍存在。
   - v1042 review 路径仍存在。
   - v1041 source receipt index 路径仍存在。

5. 声明边界
   - consumer boundary 必须保持 governance lookup only。
   - model quality claim 必须保持 bounded tiny-checkpoint claim。
   - promotion 和 approved-for-promotion 必须继续为 false。

6. 路由一致性
   - v1045 的 next step 必须指向 v1046 review。
   - v1046 通过后才生成下一步 receipt 记录路由。

## 输入输出流程

CLI 流程：

1. `locate_receipt_index_v1046` 接受 JSON 文件或 v1045 输出目录。
2. `read_json_report` 读取 v1045 index。
3. `build_randomized_holdout_..._review_v1046` 生成 review。
4. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
5. `--require-review-ready` 或 `--require-lookup-ready` 下，如果 review 不通过则返回非 0。

## 测试覆盖

聚焦测试验证：

- ready v1045 index 可以生成 `status=pass` 的 review。
- 把 `granted_use` 改成 `production_promotion` 会失败。
- 删除 source evidence digest 会失败。
- 把 source receipt path 改成不存在路径会失败。
- CLI 可以从目录定位 v1045 JSON，并输出五类 artifact。
- `require_promotion_ready=True` 仍返回 1，证明 review 没有打开 promotion。

## 运行证据

运行证据归档在：

- `e/1046/解释/receipt-index-review-v1046`
- `e/1046/图片/v1046-receipt-index-review.png`
- `e/1046/解释/说明.md`

真实 CLI 输出确认：

- `status=pass`
- `review_ready=True`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=22`
- `failed_check_count=0`

Playwright MCP 快照确认 HTML 页面中 `Status=pass`、`Failed=0`、`Review Summary` 和上游 source path 均可见。

## 一句话总结

v1046 把 v1045 receipt index 从“digest-backed lookup index”推进为“已审查、仍然 lookup-only、可以进入下一步 receipt 记录的 index review evidence”。

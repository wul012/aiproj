# v1053 publication receipt index 代码讲解

## 本版目标与边界

v1053 的目标是把 v1051 的 lookup-only receipt 和 v1052 的 contract check 组合成一个 digest-backed receipt index。

v1051 证明消费动作已经记录，v1052 证明这个消费动作可以从 v1050 review 重新生成。v1053 不再重复重建 receipt，而是把这两个源产物放到一个可查索引里，并保留路径和 SHA-256，让后续 review 可以用固定 lookup key 找到对应 receipt 与 check。

本版不训练模型，不新增 benchmark，不把 lookup-only 证据升级为生产推广许可。它只让现有治理证据更容易被后续版本消费。

## 前置链路

本版承接 v1049-v1052 的四步循环：

- v1049：把 v1047 receipt 和 v1048 check 写成 digest-backed index。
- v1050：review v1049 index，确认 lookup-only 边界。
- v1051：记录 v1050 reviewed index 的 downstream lookup-only receipt。
- v1052：重建 v1051 receipt，证明它与 v1050 review 一致。
- v1053：把 v1051 receipt 和 v1052 check 写成新的 digest-backed index。

这条链路的核心约束仍然是 `downstream_governance_lookup_only`、`promotion_ready=False`、`approved_for_promotion=False`。

## 关键文件

`src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1053.py`

这是 v1053 的核心 builder。它提供：

- `locate_receipt_v1053()`：支持输入 v1051 receipt JSON 或 receipt 输出目录。
- `locate_receipt_check_v1053()`：支持输入 v1052 check JSON 或 check 输出目录。
- `build_..._v1053()`：读取 receipt 和 check，执行字段验证，生成 index。
- `resolve_exit_code()`：支持 `--require-index-ready`、`--require-lookup-ready` 和 `--require-promotion-ready`。

`src/minigpt/..._v1053_artifacts.py`

这是输出层，负责 JSON、CSV、text、Markdown 和 HTML 渲染。CSV 只写 index row，JSON 保存完整 report，HTML 用于截图归档。

`scripts/build_..._v1053.py`

这是 CLI 入口，真实运行时用 `--receipt` 指向 `e/1051/解释/receipt-v1051`，用 `--receipt-check` 指向 `e/1052/解释/receipt-check-v1052`。

`tests/test_..._v1053.py`

这是 focused 测试，覆盖正常 index、篡改 granted use、contract check 不 ready，以及 CLI/artifact wiring。

`src/minigpt/randomized_holdout_publication_constants.py`

本版新增 v1053 next-step 常量，把 index pass 后的下一步路由到 v1053 review。

## 核心数据结构

v1053 report 的核心字段包括：

- `summary`：给 CLI 和 HTML 使用的压缩摘要。
- `receipt_index`：核心 index 对象，包含 index row、source evidence row、lookup scope 和下一步。
- `receipt_index_rows`：可被后续 review 消费的 lookup row。
- `source_evidence_rows`：v1051 receipt 和 v1052 check 的路径、SHA-256 与状态。
- `check_rows`：25 个字段/边界检查结果。

index row 的关键字段是：

- `receipt_index_id`：本版 index 的稳定 ID。
- `lookup_key`：由固定 prefix 加 v1051 receipt id 组成。
- `receipt_id` / `receipt_status`：来自 v1051 receipt。
- `granted_use`：固定为 `downstream_governance_lookup_only`。
- `contract_check_ready`：来自 v1052 check。
- `promotion_ready`：固定为 `False`。

## 运行流程

1. CLI 定位 v1051 receipt 和 v1052 check。
2. builder 读取两个 JSON，并分别抽取 `summary` 与 `receipt`。
3. `_checks()` 执行 readiness、decision、contract check、lookup-only、source path、no-promotion 和 next-step 检查。
4. `_index()` 在所有检查通过时生成一个 lookup row 和两条 source evidence row。
5. `_summary()` 把 index 状态压缩成报告摘要。
6. artifact writer 输出 JSON/CSV/text/Markdown/HTML。

## 关键断言

v1053 的关键保护点包括：

- `receipt_decision_ready`：v1051 receipt 必须是 ready decision。
- `receipt_check_decision_ready`：v1052 contract check 必须是 passed decision。
- `granted_use_lookup_only`：receipt、receipt body、check original/rebuilt use 都必须是 lookup-only。
- `lookup_key_count`：lookup key 必须正好一个。
- `source_*_file_exists`：所有追溯文件必须仍存在。
- `promotion_still_false`：summary、receipt、check original/rebuilt promotion 字段都必须为 false。
- `source_next_steps_match`：v1051 必须指向 check，v1052 必须指向 index。

这些断言让 v1053 不只是“把文件列出来”，而是先确认文件关系、边界字段和下一步路由都没有漂移。

## 测试覆盖

focused v1053 测试覆盖 4 个场景：

- ready receipt + ready contract check 可以生成 index。
- 篡改 `granted_use` 会触发 lookup-only 失败。
- contract check 不 ready 会触发 `contract_check_ready` 失败。
- CLI 和 artifact writer 可以生成 JSON、CSV、text、Markdown、HTML。

真实证据还使用 `e/1051` 和 `e/1052` 的归档产物跑了一次 CLI，避免只依赖测试夹具。

## 运行证据

真实 CLI 证据在：

- `e/1053/解释/receipt-index-v1053/`

Playwright MCP 截图在：

- `e/1053/图片/v1053-receipt-index.png`

页面显示：

- `Status=pass`
- `Index ready=True`
- `Lookup keys=1`
- `Contract=True`
- `Evidence=2`
- `Failed=0`

## 边界说明

v1053 的 pass 只表示 receipt/check 可以被索引并保持 lookup-only 边界。它不代表模型训练效果提升，不代表真实部署能力增强，也不代表生产推广许可。

一句话总结：v1053 把 v1051/v1052 两个治理证据收成 digest-backed lookup index，为后续 review 提供稳定入口。

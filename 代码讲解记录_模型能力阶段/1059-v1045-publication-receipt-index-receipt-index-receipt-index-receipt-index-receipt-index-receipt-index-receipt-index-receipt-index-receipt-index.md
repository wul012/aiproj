# v1045 publication receipt index 代码讲解

## 本版目标和边界

v1045 的目标是把 v1043 downstream lookup-only receipt 和 v1044 receipt contract check 写入新的 digest-backed receipt index。

它解决的问题是：v1043 receipt 已记录，v1044 contract check 已证明 receipt 可由 v1042 review 重建，但后续 review 需要一个稳定的 index artifact，统一记录 lookup key、source receipt、source contract check、SHA-256 digest、lookup-only use 和 no-promotion 边界。

本版不做：

- 不训练模型。
- 不新增 benchmark 或 replay。
- 不把 index ready 解释成模型质量提升。
- 不开启 production promotion。

## 前置链路

v1045 直接承接：

- v1043：记录 downstream lookup-only consumer receipt。
- v1044：从 v1042 source review 重建 v1043 receipt，并逐项确认 original/rebuilt 一致。
- v1045：把 receipt 和 contract check 合并成新的 receipt index，供下一步 review 使用。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1045.py`
  - v1045 index builder。
  - 读取 v1043 receipt 和 v1044 contract check，执行 readiness、lookup-only、source path、digest 和 no-promotion 检查。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1045_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 记录 index row，HTML 用于 Playwright MCP 截图。

- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1045.py`
  - CLI 入口。
  - 支持 `--receipt`、`--receipt-check`、`--require-index-ready`、`--require-lookup-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1045.py`
  - 覆盖 ready path、granted use 漂移、contract check not ready、CLI 和 output wiring。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1045 next-step 常量，路由到下一步 review。

## 维护性说明

v1045 源码只依赖 v1043 receipt、v1044 receipt check 和公共 helper。测试侧复用 v1044 已经本地化的 ready receipt helper，不直接导入 v1043/v1042 历史测试链。

这个处理是为了避免历史 governance 模块链越来越长后，在 pytest assertion rewrite 下出现递归过深。v1045 的职责是索引 v1043/v1044 两个已经稳定的 artifact，不需要重新加载更早 builder。

## 核心数据结构

`receipt_index` 字段包含：

- `index_ready`：本版 index 是否可消费。
- `receipt_index_id`：稳定 index ID。
- `lookup_scope`：固定为 `downstream_governance_lookup_only`。
- `lookup_key_count`：当前为 1。
- `receipt_index_rows`：下游按 lookup key 查询的主行。
- `source_evidence_rows`：receipt 和 receipt_check 的路径与 SHA-256。
- `lookup_ready`：是否可以作为下游 lookup 输入。
- `contract_check_ready`：v1044 contract check 是否 ready。
- `promotion_ready=False` 和 `approved_for_promotion=False`：继续阻断推广。

`summary` 字段把核心状态压成 CLI/HTML 直接展示的摘要：

- ready key
- receipt index id
- lookup scope
- lookup key count
- receipt status
- granted use
- source evidence count
- lookup ready
- contract check ready
- promotion state
- next step
- passed/failed check count

## 检查项说明

`_checks` 一共保护 25 个条件，重点包括：

- v1043 receipt 文件存在。
- v1044 receipt check 文件存在。
- receipt status/decision/ready key 都 ready。
- contract check status/decision/summary 都 ready。
- receipt status 与 contract check 的 original/rebuilt status 一致。
- granted use 在 receipt、receipt body、contract original/rebuilt 四处都是 lookup-only。
- lookup key count 为 1。
- source evidence count 为 2。
- v1042 source review、v1041 source index、v1039 source receipt、v1040 source check、v1038 source review、v1037 origin index 路径仍存在。
- consumer boundary 和 model quality claim 不漂移。
- promotion 字段持续 false。
- v1043/v1044 next_step 路由符合“receipt -> check -> index”顺序。

## 输入输出流程

CLI 流程：

1. `locate_receipt_v1045` 支持 receipt JSON 或输出目录。
2. `locate_receipt_check_v1045` 支持 check JSON 或输出目录。
3. `read_json_report` 读取两个源 artifact。
4. `build_randomized_holdout_..._v1045` 执行检查并构造 index。
5. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
6. `--require-index-ready` 或 `--require-lookup-ready` 下，失败时返回非 0。

## 测试覆盖

聚焦测试验证：

- ready receipt + ready contract check 可以生成 index。
- receipt `granted_use` 被改成 production promotion 会失败。
- contract check 的 `contract_check_ready=False` 会失败。
- CLI 能从目录定位输入并输出五类 artifact。
- `require_promotion_ready=True` 仍会返回 1，证明本版没有打开 promotion。

## 运行证据

运行证据归档在：

- `e/1045/解释/receipt-index-v1045`
- `e/1045/图片/v1045-receipt-index.png`

真实 CLI 输出显示：

```text
index_ready=True
lookup_scope=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

Playwright MCP 截图确认 HTML 页面可读，页面展示 `Index ready=True`、`Lookup keys=1`、`Contract=True`、`Evidence=2`、`Failed=0`，并包含 Receipt Index Rows、Source Evidence 和 Checks 三张表。

## 一句话总结

v1045 把 v1043 receipt 和 v1044 contract check 变成下一层可 review 的 digest-backed receipt index，继续保持 lookup-only 和 no-promotion 边界。

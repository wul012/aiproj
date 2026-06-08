# v989 publication receipt index receipt index

## 目标与边界

v989 的目标是把 v987 lookup-only receipt 和 v988 receipt contract check 收成一个 receipt index。v988 已经证明 v987 receipt 可以从 v986 review 重新推导；v989 则让这份 receipt/check pair 变成后续模块可查询、可审计、可带 digest 消费的索引条目。

本版不训练模型，不更新 checkpoint，不改变 baseline/candidate 选择，也不把 lookup-only receipt 升级成 production promotion。

## 前置路线

1. v987 记录 v986-reviewed receipt index 的 downstream receipt。
2. v988 重新构造 v987 receipt 并确认 contract check 通过。
3. v989 将 v987 receipt 与 v988 check 收进 receipt index。

这条路线与 v983-v985 的结构一致：先 record receipt，再 check receipt，最后 index receipt。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989.py`
  - 核心 index builder。
  - 校验 v987 receipt 和 v988 check 的状态、用途、路径、source evidence、no-promotion 边界。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
- `scripts/build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989.py`
  - CLI 入口。
  - 支持 `--receipt`、`--receipt-check`、`--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v989.py`
  - 覆盖 ready index、granted use 篡改、source review 缺失、contract check 未 ready、CLI 失败码和输出渲染。

## 核心数据结构

`receipt_index` 是 v989 的核心结构：

- `index_ready`
  - 所有检查通过后为 `True`。
- `receipt_index_id`
  - 固定为 `randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-v989`。
- `lookup_scope`
  - 固定为 `downstream_governance_lookup_only`。
- `receipt_index_rows`
  - 记录可查询的 receipt row。
- `source_evidence_rows`
  - 保存 v987 receipt 和 v988 contract check 的 path、SHA-256、status。
- `lookup_ready`
  - source receipt 有且仅有 1 个 lookup key 时为 `True`。
- `contract_check_ready`
  - v988 check 通过时为 `True`。
- `promotion_ready`
  - 固定为 `False`。

## Receipt Index Row

v989 的 index row 包含：

- `receipt_index_id`
- `lookup_key`
  - 命名空间是 `receipt-index-receipt:`。
- `receipt_id`
- `receipt_status`
- `granted_use`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
  - 指向 v986 review。
- `source_prior_receipt_path`
  - 指向更早的 v983 receipt。
- `source_prior_receipt_check_path`
  - 指向更早的 v984 check。
- `contract_check_ready`
- `promotion_ready`

这个 row 是后续 review 或 publication 的主消费对象。

## 核心检查

v989 的 `_checks()` 保护以下内容：

- v987 receipt 文件必须存在。
- v988 check 文件必须存在。
- receipt 顶层 status 和 decision 必须 ready。
- receipt summary 与 receipt body 必须 ready。
- receipt status 必须为 `publication_receipt_index_lookup_receipted`。
- v988 contract check 必须 pass。
- contract check summary 必须 ready。
- receipt status 必须与 check 的 original/rebuilt status 一致。
- granted use 必须始终是 lookup-only。
- lookup key count 必须为 1。
- consumer receipt row count 必须为 1。
- source evidence count 必须为 2。
- v986 source review、v983 source receipt、v984 source check 必须仍存在。
- consumer boundary 和 model quality claim 不允许扩大。
- promotion flags 必须全部为 `False`。
- source receipt/check failed count 必须为 0。
- source next step 必须符合 v987 -> v988 -> v989 的路由。

这些检查让 index 不是简单列表，而是带边界验证的可查询证据。

## 输入输出流程

CLI 流程：

```text
v987 receipt dir/json
v988 check dir/json
 -> locate source artifacts
 -> read_json_report
 -> build receipt index
 -> write json/csv/txt/md/html
 -> resolve_exit_code
```

JSON 是后续 review 的主输入；CSV 适合快速查看 index row；Markdown/HTML 供人工审阅；text 供命令行核对关键字段。

## 测试覆盖

测试覆盖：

- ready receipt/check pair 能生成 `status=pass` 的 receipt index。
- 篡改 `granted_use` 会触发 `granted_use_lookup_only`。
- 改坏 source review path 会触发 `source_receipt_index_review_file_exists`。
- 关闭 check readiness 会触发 `contract_check_ready`。
- CLI 在 `--require-index-ready` 下遇到失败返回 `1`。
- artifact writer 生成五类输出，并能渲染关键段落。

测试会从 v988 的 ready fixture 开始构造 receipt/check pair，因此覆盖的是跨版本链路。

## 运行证据

真实运行证据写入：

```text
e/989/解释/publication-receipt-index-receipt-index-v989/
```

核心结果：

```text
status=pass
index_ready=True
lookup_key_count=1
source_evidence_count=2
contract_check_ready=True
promotion_ready=False
passed_check_count=23
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/989/图片/v989-randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index.png
```

## 一句话总结

v989 把 v987/v988 的 lookup-only receipt 证据收成 digest-backed receipt index，让后续版本可以稳定查询它，同时继续阻止生产晋升边界被误打开。

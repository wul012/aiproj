# v997 publication receipt index receipt index publication index receipt index

本版目标是把 v995 receipt 和 v996 contract check 合并成一个 receipt index。它解决的是后续 review 不应同时手动追踪 receipt 与 check 两个文件的问题：v997 用一条 `publication-index-receipt:` lookup row 和两条 source evidence 绑定这两个源产物。

本版不训练模型，不改 checkpoint，不做 production promotion。

## 前置路线

v995 记录 v994 review 后的 lookup-only consumer receipt。v996 从 v994 review 重新构建 v995 receipt，并证明 original/rebuilt 字段一致。v997 在两者都通过时创建 receipt index。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.py`
  - 核心 index builder。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.py`
  - CLI 入口，支持 `--require-index-ready`、`--require-lookup-ready` 和 `--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v997.py`
  - 覆盖 ready index、granted use 篡改、contract check 不 ready、输出和 CLI。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v997 下一步路由。
- `src/minigpt/__init__.py`
  - 暴露 v997 build/write 包级入口。

## 核心结构

`receipt_index` 包含：

- `index_ready`
- `receipt_index_id`
- `lookup_scope=downstream_governance_lookup_only`
- `lookup_key_count`
- `receipt_index_rows`
- `source_evidence_rows`
- `receipt_path`
- `receipt_check_path`
- `receipt_id`
- `receipt_status`
- `granted_use`
- `lookup_ready`
- `contract_check_ready`
- `promotion_ready=False`
- `approved_for_promotion=False`
- `next_step`

`receipt_index_rows` 是后续 review 主要消费对象；`source_evidence_rows` 对 v995 receipt 和 v996 check 计算 SHA-256，供后续确认源文件未漂移。

## 检查范围

v997 检查 receipt/check 文件存在、v995 receipt ready、v996 contract check ready、receipt status 与 contract check 中 original/rebuilt status 一致、granted use 仍是 lookup only、lookup key 只有一条、source evidence 为两条、source review/publication/check 路径仍存在、bounded claim 和 no-promotion 字段不变。

真实运行输出显示 `status=pass`、`index_ready=True`、`lookup_key_count=1`、`source_evidence_count=2`、`failed_check_count=0`、`passed_check_count=22`。

## 运行证据

运行证据写入 `e/997/解释/说明.md` 和 `e/997/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-v997/`。Playwright MCP 截图保存在 `e/997/图片/`，证明 HTML 报告可打开并展示 index row、source evidence 和 checks 表。

## 一句话总结

v997 把 v995/v996 证据合并成 lookup-only receipt index，让后续 review 有了单一、可校验、不可 promotion 的入口。

# v1047 publication receipt 代码讲解

## 本版目标和边界

v1047 的目标是读取 v1046 receipt index review，记录一个 downstream lookup-only receipt。

它解决的问题是：v1046 已经 review 了 v1045 digest-backed receipt index，但后续 contract check 需要一个稳定 receipt artifact，明确 consumer、requested use、granted use、source review digest、lookup keys、source evidence 和 no-promotion 边界。v1047 就是这份 receipt。

本版不做：

- 不训练模型。
- 不新增 benchmark。
- 不修改 v1046 review。
- 不允许 production promotion。
- 不把 receipt ready 解释为模型能力提升。

## 前置链路

v1047 直接承接：

- v1045：生成 digest-backed receipt index。
- v1046：只读 review v1045 index，确认 lookup-only、source path、source evidence、promotion=false。
- v1047：把 v1046 review 记录成 downstream consumer receipt，供 v1048 contract check 重建验证。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1047.py`
  - v1047 receipt builder。
  - 读取 v1046 review，检查 review status、lookup-only use、source evidence、source path、promotion=false 和 next-step。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1047_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - CSV 记录 consumer receipt，HTML 用于 Playwright MCP 截图。

- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1047.py`
  - CLI 入口。
  - 支持输入 v1046 review JSON 或目录，支持 `--consumer-name`、`--requested-use`、`--require-receipt-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1047.py`
  - 覆盖 ready path、requested use 漂移、source review path 漂移、source evidence status 漂移、CLI failure 和 output wiring。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1047 next-step 常量，路由到下一步 receipt contract check。

## 核心数据结构

`receipt` 字段是本版主输出：

- `receipt_ready`：所有检查通过时为 true。
- `receipt_id`：稳定 receipt ID。
- `receipt_type`：本链路 receipt 类型。
- `receipt_status`：lookup receipted 状态。
- `consumer_name`：默认 downstream lookup reader。
- `requested_use`：请求用途，必须是 `downstream_governance_lookup_only`。
- `granted_use`：实际批准用途，通过时仍是 lookup-only。
- `receipt_index_review_path`：v1046 review 路径。
- `receipt_index_review_sha256`：v1046 review 文件 digest。
- `receipt_index_row_count`：当前为 1。
- `source_evidence_count`：当前为 2。
- `lookup_keys`：继承 v1046 review 中的 lookup key。
- `promotion_ready=False` 和 `approved_for_promotion=False`：继续阻断生产推广。
- `source_receipt_index_path`、`source_receipt_path`、`source_receipt_check_path`、`source_review_path`、`source_receipt_index_origin_path`：保留完整上游证据路径。
- `next_step`：通过时路由到 v1047 receipt contract check。

`consumer_receipts` 是后续消费方最常读的表：

- `consumer_name`
- `lookup_key`
- `receipt_index_id`
- `source_receipt_id`
- `receipt_id`
- `granted_use`
- `promotion_ready`
- `receipt_status`

## 检查项说明

`_checks` 保护 25 个条件，重点包括：

- v1046 review 文件必须存在。
- v1046 review status 和 decision 必须 ready。
- v1046 summary ready key 和 review body 必须同时 ready。
- `review_status` 必须是 lookup-only receipt recording approval。
- `requested_use` 必须是 downstream governance lookup only。
- summary 和 review body 的 `granted_use` 都必须 lookup-only。
- receipt index lookup 和 contract check 都必须 ready。
- index row 数量为 1。
- source evidence 数量为 2，digest 存在且 status 全部 pass。
- lookup keys 必须使用 v1045 source namespace。
- index rows 的 `promotion_ready` 必须全为 false。
- v1045 index、v1043 receipt、v1044 check、v1042 review、v1041 origin index 路径仍存在。
- consumer boundary 和 model quality claim 不漂移。
- v1046 next-step 必须指向 v1047 receipt。

## 输入输出流程

CLI 流程：

1. `locate_receipt_index_review_v1047` 接受 v1046 JSON 或输出目录。
2. `read_json_report` 读取 v1046 review。
3. `build_randomized_holdout_..._receipt_v1047` 生成 receipt。
4. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
5. `--require-receipt-ready` 下，如果 receipt 不通过则返回非 0。

## 测试覆盖

聚焦测试验证：

- ready v1046 review 可以生成 `status=pass` receipt。
- `requested_use=production_promotion` 会失败。
- source review path 漂移会失败。
- source evidence status 变成 fail 会失败。
- CLI 在坏 review + `--require-receipt-ready` 下返回 1，同时仍写出失败 artifact。
- 输出 writer 和 CLI wiring 都可用。
- `require_promotion_ready=True` 仍返回 1，证明本版没有打开 promotion。

## 运行证据

运行证据归档在：

- `e/1047/解释/receipt-v1047`
- `e/1047/图片/v1047-receipt.png`
- `e/1047/解释/说明.md`

真实 CLI 输出确认：

- `status=pass`
- `receipt_ready=True`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP 快照确认 HTML 页面中 `Status=pass`、`Receipt ready=True`、`Failed=0`、`Receipt Boundary` 和完整上游路径均可见。

## 一句话总结

v1047 把 v1046 review 的 lookup-only 批准落成可签收的 downstream receipt，为下一步 contract check 提供稳定源证据。

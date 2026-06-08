# v998 publication receipt index receipt index publication index receipt index review

本版目标是复核 v997 生成的 publication index receipt index，确认它可以作为下一步 receipt 记录的输入。它解决的问题是：v997 已经把 v995 receipt 和 v996 contract check 合并成一个 lookup-only receipt index，但在后续记录 receipt 之前，还需要证明该索引没有路径漂移、digest 漂移、lookup scope 扩张或 promotion 字段被打开。

本版不训练模型，不修改 checkpoint，不声称模型质量提升，也不做 production promotion。它只验证治理产物自身的一致性和消费边界。

## 前置路线

v995 记录 v994 review 后的 publication index lookup-only receipt。v996 从 v994 review 重新构建 v995 receipt，证明 original/rebuilt 字段一致。v997 把 v995 receipt 和 v996 contract check 合并成一个 `publication-index-receipt:` receipt index。v998 站在 v997 之后，先 review 这个 receipt index，再把下一步路由到 receipt 记录。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998.py`
  - v998 核心 review builder。它读取 v997 JSON，拆出 `summary`、`receipt_index`、`receipt_index_rows` 和 `source_evidence_rows`，生成 check rows、review summary 和 interpretation。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。CSV 保存逐项 check，HTML 用于 Playwright 截图证明报告能打开并展示关键字段。
- `scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v998.py`
  - CLI 入口。支持输入 v997 JSON 或输出目录，支持 `--require-review-ready`、`--require-receipt-index-ready` 和 `--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_review_v998.py`
  - 覆盖 ready review、bad digest、lookup scope 篡改、body/row path 漂移、CLI 失败退出和输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v998 下一步常量：`record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_v998`。
- `src/minigpt/__init__.py`
  - 暴露 v998 build/write 包级懒加载入口。

## 核心数据结构

输入是 v997 的 receipt index report。核心字段包括：

- `summary.randomized_holdout_..._receipt_index_v997_ready`
- `summary.lookup_scope`
- `summary.granted_use`
- `summary.lookup_key_count`
- `summary.contract_check_ready`
- `summary.promotion_ready`
- `receipt_index.receipt_index_rows`
- `receipt_index.source_evidence_rows`
- `receipt_index.receipt_path`
- `receipt_index.receipt_check_path`

v998 输出的 `review` 对象保存：

- `review_ready`
- `review_id`
- `review_status=approved_for_publication_index_receipt_index_receipt_lookup_only`
- `receipt_index_path`
- `receipt_index_id`
- `receipt_index_row_count`
- `source_evidence_count`
- `lookup_keys`
- `receipt_index_ready`
- `lookup_ready`
- `contract_check_ready`
- `promotion_ready=False`
- `approved_for_promotion=False`
- `allowed_use=downstream_governance_lookup_only`
- `blocked_uses`
- `source_receipt_path`
- `source_receipt_check_path`
- `next_step`

这些字段不是模型能力证据，而是后续 receipt 记录可以消费的治理边界。

## 检查逻辑

v998 的 `_checks()` 逐项验证：

- v997 receipt index 文件存在。
- v997 report status 和 decision 是 ready。
- summary ready flag 与 body `index_ready` 同时为真。
- `lookup_scope` 和 `granted_use` 仍然是 downstream governance lookup only。
- `lookup_ready` 和 `contract_check_ready` 都为真。
- 只有一条 index row，lookup key 必须使用 `publication-index-receipt:` 命名空间。
- index row 不允许 promotion。
- source evidence 必须是两条、状态 pass、SHA-256 合法、文件仍存在。
- `receipt_path` 与 row 的 `source_receipt_path` 必须一致。
- `receipt_check_path` 与 row 的 `source_receipt_check_path` 必须一致。
- source review 文件仍存在。
- consumer boundary 和 model quality claim 仍然保持 bounded。
- summary/body/approved 三处 promotion 字段都为 false。
- v997 的 failed check count 必须为 0。
- v997 next step 必须指向本版 review。

新增的 `source_paths_match_rows` 很关键：它防止有人只改 index body 或只改 row，让同一个 report 内部出现两个不同来源。

## 运行证据

真实运行使用 v997 归档目录生成 v998 证据：

```powershell
python scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_v998.py e/997/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-v997 --out-dir e/998/解释/publication-receipt-index-receipt-index-publication-index-receipt-index-review-v998 --require-review-ready --require-receipt-index-ready --force
```

输出显示 `status=pass`、`review_ready=True`、`receipt_index_ready=True`、`lookup_key_count=1`、`source_evidence_count=2`、`contract_check_ready=True`、`promotion_ready=False`、`failed_check_count=0`、`passed_check_count=24`。

Playwright MCP 打开 HTML 后保存快照和截图到 `e/998`。这证明报告页面可读，关键状态、边界和 checks 表可直接检查。

## 测试覆盖

测试不是只验证 happy path：

- ready review 确认 v997 生成的索引可以通过 v998。
- bad digest 测试保护 source evidence SHA-256。
- lookup scope 篡改测试阻止治理 lookup 扩张成 production promotion。
- body/row path 漂移测试保护 `receipt_path` 和 row source path 的一致性。
- CLI 失败退出测试确认 `--require-review-ready` 在失败时返回 1，同时仍写出失败报告。
- 输出测试覆盖 JSON/CSV/TXT/Markdown/HTML 和 CLI wiring。

## 一句话总结

v998 把 v997 的 receipt index 从“已生成”推进到“已复核可记录”，并继续把模型质量边界限定在 lookup-only 治理证据内。

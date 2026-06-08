# v986 publication receipt index review

## 目标与边界

v986 的目标是审阅 v985 receipt index。v985 已经把 v983 receipt 和 v984 receipt contract check 合并成一个 receipt index；v986 负责判断这个 index 是否可以进入下一步 lookup-only receipt flow。

本版不做模型训练，不更新 checkpoint，不声明模型能力提升，也不把 lookup-only 证据升级成 production promotion。

## 前置路线

1. v983 记录 lookup-only receipt。
2. v984 重建检查 receipt。
3. v985 将 receipt 和 receipt check 收成 receipt index。
4. v986 对 receipt index 做 review。

v986 的位置类似 v982 对 v981 publication index 的审阅，只是对象从 publication index 换成 receipt index。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_review_v986.py`
  - 核心 review builder。
  - 读取 v985 index，检查 index ready、lookup-only、source evidence、路径和 no-promotion 边界。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_review_v986_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
- `scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_v986.py`
  - CLI 入口。
  - 支持 `--require-review-ready`、`--require-receipt-ready`、`--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_review_v986.py`
  - 覆盖 ready review、digest 篡改、lookup scope 篡改、source receipt 缺失、CLI 失败码和输出渲染。

## 核心数据结构

`review` 是 v986 的核心结构，关键字段包括：

- `review_ready`
  - 只有所有检查通过才为 `True`。
- `review_status`
  - ready 时为 `approved_for_publication_receipt_index_receipt_lookup_only`。
- `receipt_index_path`
  - 指向 v985 JSON。
- `receipt_index_row_count`
  - 固定要求为 1。
- `source_evidence_count`
  - 固定要求为 2。
- `lookup_keys`
  - 要求使用 `receipt-index:` 命名空间。
- `receipt_ready`
  - 表示可进入下一步 receipt 记录。
- `allowed_use`
  - 固定为 `downstream_governance_lookup_only`。
- `promotion_ready`
  - 固定为 `False`。

## 核心检查

v986 的 `_checks()` 保护以下边界：

- v985 receipt index 文件必须存在。
- index 顶层 `status` 和 `decision` 必须 ready。
- summary 与 index body 都必须 ready。
- `lookup_scope` 必须保持 `downstream_governance_lookup_only`。
- `granted_use` 必须保持 `downstream_governance_lookup_only`。
- lookup 与 contract check 必须 ready。
- receipt index row 必须正好一行。
- lookup key 必须使用 `receipt-index:` 命名空间。
- source evidence 必须两行、状态 pass、SHA-256 格式正确、文件仍存在。
- 源 receipt、receipt check、source review、source publication、source publication check 必须仍存在。
- consumer boundary 和 model quality claim 不能扩大。
- promotion 和 approved_for_promotion 必须保持 `False`。
- source failed check count 必须为 0。
- v985 next step 必须指向 v986 review。

这些检查让 v986 的 review 不只是“批准下一步”，而是确认 receipt index 仍保留可复核的上游证据链。

## 输入输出流程

CLI 流程：

```text
receipt index dir/json -> locate_receipt_index_v986
read_json_report -> builder
builder -> review/check_rows/summary/interpretation
artifact writer -> json/csv/txt/md/html
resolve_exit_code -> require flags
```

JSON 是后续模块的主输入；CSV 记录检查行；Markdown/HTML 用于人工审阅；text 用于命令行快速核对。

## 运行证据

真实运行输出在：

```text
e/986/解释/publication-receipt-index-review-v986/
```

关键结果：

```text
status=pass
review_ready=True
review_status=approved_for_publication_receipt_index_receipt_lookup_only
receipt_ready=True
lookup_key_count=1
source_evidence_count=2
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/986/图片/v986-randomized-holdout-publication-receipt-packet-index-publication-receipt-index-review.png
```

## 测试覆盖

测试覆盖了五类风险：

- ready receipt index 可以通过 review。
- source evidence digest 被篡改会失败。
- lookup scope 被改成 promotion 会失败。
- source receipt 路径缺失会失败。
- CLI 在 `--require-review-ready` 下遇到失败报告会返回 1，并保留诊断输出。

## 一句话总结

v986 把 v985 receipt index 从“可查”推进为“可审阅、可进入下一步 lookup-only receipt flow 的索引证据”。

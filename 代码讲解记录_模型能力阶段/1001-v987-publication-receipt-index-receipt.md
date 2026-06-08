# v987 publication receipt index receipt

## 目标与边界

v987 的目标是记录 v986-reviewed receipt index 的 downstream receipt。v986 已经批准 v985 receipt index 可以进入 lookup-only receipt flow；v987 负责把这个批准转成明确的消费者接收记录。

本版不做模型训练，不更新 checkpoint，不声明模型能力提升，也不把 lookup-only 证据升级成 production promotion。

## 前置路线

1. v985 将 v983 receipt 和 v984 contract check 收成 receipt index。
2. v986 review receipt index，确认它仍保持 lookup-only、source evidence 和 no-promotion 边界。
3. v987 记录下游消费者 receipt。

v987 与 v983 的角色相似，都是“在 review 后记录 receipt”；区别是 v987 的对象是 receipt index，而不是 publication index。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.py`
  - 核心 receipt builder。
  - 读取 v986 review，生成 receipt、consumer receipts、summary 和 interpretation。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
- `scripts/record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.py`
  - CLI 入口。
  - 支持 `--consumer-name`、`--requested-use`、`--require-receipt-ready` 和 `--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v987.py`
  - 覆盖 ready receipt、requested use 篡改、source receipt 缺失、CLI 失败码和输出渲染。

## 核心数据结构

`receipt` 是 v987 的核心结构，关键字段包括：

- `receipt_ready`
  - 全部检查通过后为 `True`。
- `receipt_id`
  - 固定为 `randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-v987`。
- `receipt_status`
  - ready 时为 `publication_receipt_index_lookup_receipted`。
- `consumer_name`
  - 默认 `publication_receipt_index_governance_lookup_reader`。
- `requested_use`
  - 默认 `downstream_governance_lookup_only`。
- `granted_use`
  - 只允许 `downstream_governance_lookup_only`。
- `receipt_index_review_path`
  - 指向 v986 review JSON。
- `lookup_keys`
  - 来自 v986 review，必须是 `receipt-index:` 命名空间。
- `blocked_uses`
  - 保留 production promotion、model quality expansion、training data claim expansion 三类禁止用途。
- `promotion_ready`
  - 固定为 `False`。

## 核心检查

v987 的 `_checks()` 保护以下边界：

- v986 review 文件必须存在。
- review 顶层 `status` 和 `decision` 必须 ready。
- review summary 与 review body 必须 ready。
- review status 必须为 `approved_for_publication_receipt_index_receipt_lookup_only`。
- `requested_use` 必须保持 lookup-only。
- blocked uses 必须完整。
- receipt 和 lookup 必须 ready。
- contract check 必须 ready。
- receipt index row 必须正好一行。
- source evidence 必须正好两行。
- lookup key 必须使用 `receipt-index:` 命名空间。
- index rows 不能 promotion。
- source receipt 和 source receipt check 必须仍存在。
- consumer boundary 和 model quality claim 不能扩大。
- source failed check count 必须为 0。
- v986 next step 必须指向 v987 receipt。

这组检查让 receipt 记录不只是“登记消费者”，还会复查用途、证据、路径和 no-promotion 边界。

## 输入输出流程

CLI 流程：

```text
review dir/json -> locate_receipt_index_review_v987
read_json_report -> builder
builder -> receipt/consumer_receipts/check_rows/summary
artifact writer -> json/csv/txt/md/html
resolve_exit_code -> require flags
```

JSON 是后续 contract check 的主输入；CSV 记录 consumer receipt 行；Markdown/HTML 用于人工审阅；text 用于命令行快速核对。

## 运行证据

真实运行输出在：

```text
e/987/解释/publication-receipt-index-receipt-v987/
```

关键结果：

```text
status=pass
receipt_ready=True
receipt_status=publication_receipt_index_lookup_receipted
consumer_name=publication_receipt_index_governance_lookup_reader
granted_use=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=20
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/987/图片/v987-randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt.png
```

## 测试覆盖

测试覆盖四类风险：

- ready review 可以生成 ready receipt。
- requested use 被改成 production promotion 会失败。
- source receipt 路径缺失会失败。
- CLI 在 `--require-receipt-ready` 下遇到失败报告会返回 1，并保留诊断输出。

## 一句话总结

v987 把 v986 的审阅批准推进为“指定下游消费者已经 lookup-only 接收 receipt index”的可复核记录。

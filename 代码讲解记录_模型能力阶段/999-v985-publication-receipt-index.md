# v985 publication receipt index

## 目标与边界

v985 的目标是把 v983 receipt 和 v984 receipt contract check 合并成一个 receipt index。v983 证明“下游消费者已收到并只能 lookup-only 使用 publication index”，v984 证明“这个 receipt 可以从源 review 重建”。v985 负责把这两个结论变成一个可查索引，方便后续 review 或下游治理链继续消费。

本版不做模型训练，不更新 checkpoint，不声明模型能力提升，不把 lookup-only 证据升级成 production promotion。

## 前置路线

1. v981 将 v979 publication 和 v980 contract check 收成 publication index。
2. v982 review v981 index，确认它可以被 receipt。
3. v983 记录 lookup-only receipt。
4. v984 重建检查 v983 receipt。
5. v985 将 receipt 与 receipt check 收成 receipt index。

这条路线的重点是治理证据可追溯，不是模型能力扩张。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_v985.py`
  - 核心 builder。
  - 负责读取 receipt/check 报告、执行 23 条检查、生成 `receipt_index_rows` 和 `source_evidence_rows`。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_v985_artifacts.py`
  - 负责 JSON、CSV、text、Markdown、HTML 输出。
  - core 模块不承担渲染职责，避免继续把单文件做大。
- `scripts/build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_v985.py`
  - CLI 入口。
  - 支持 `--receipt`、`--receipt-check`、`--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_v985.py`
  - 覆盖 ready 路径、granted use 篡改、source review 丢失、contract check 未 ready、CLI 失败码和输出渲染。

## 核心数据结构

`receipt_index` 是 v985 的核心结构，关键字段包括：

- `index_ready`
  - 只有全部检查通过才为 `True`。
- `receipt_index_id`
  - 固定为 `randomized-holdout-publication-receipt-packet-index-publication-receipt-index-v985`。
- `lookup_scope`
  - 固定保持 `downstream_governance_lookup_only`。
- `receipt_index_rows`
  - 下游实际查找的索引行。
  - 记录 receipt id、receipt status、granted use、源 receipt/check/review/publication/check 路径。
- `source_evidence_rows`
  - 对 v983 receipt 和 v984 receipt check 计算 SHA-256。
  - 这是后续模块判断源证据是否变动的只读依据。
- `promotion_ready`
  - 固定为 `False`。

## 核心检查

v985 的 `_checks()` 保护以下边界：

- v983 receipt 文件必须存在。
- v984 receipt check 文件必须存在。
- receipt 顶层 `status` 和 `decision` 必须 ready。
- receipt summary 与 receipt body 都必须 ready。
- receipt check 必须通过，且 `contract_check_ready=True`。
- receipt status 必须和 v984 的 original/rebuilt status 一致。
- `granted_use` 必须在 summary、receipt body、original check、rebuilt check 中全部保持 lookup-only。
- lookup key count 必须为 1。
- consumer receipt 行数必须为 1。
- source evidence count 必须为 2。
- source index review、source publication、source publication check 路径必须仍存在。
- consumer boundary 与 model quality claim 不能被扩大。
- promotion 与 approved_for_promotion 必须保持 `False`。
- 源 receipt/check 的 failed check count 必须为 0。
- 源 next step 必须从 receipt -> check -> index 正常衔接。

这些检查让 v985 不是“把两个 JSON 拼起来”，而是确认它们仍然能作为下游 lookup-only 索引入口。

## 输入输出流程

CLI 流程：

```text
--receipt -> locate_receipt_v985 -> read_json_report
--receipt-check -> locate_receipt_check_v985 -> read_json_report
builder -> receipt_index/check_rows/summary/interpretation
artifact writer -> json/csv/txt/md/html
resolve_exit_code -> require flags
```

输出 JSON 是后续模块消费的主产物。CSV 只承载索引行，Markdown/HTML 用于人工审阅，text 用于命令行快速核对。

## 运行证据

真实运行输出在：

```text
e/985/解释/publication-receipt-index-v985/
```

关键结果：

```text
status=pass
index_ready=True
lookup_scope=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
contract_check_ready=True
promotion_ready=False
passed_check_count=23
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/985/图片/v985-randomized-holdout-publication-receipt-packet-index-publication-receipt-index.png
```

## 测试覆盖

测试覆盖了五类风险：

- 正常 receipt + receipt check 可以生成 ready index。
- 篡改 `granted_use` 会失败，防止 lookup-only 被升级。
- 删除 source review 路径会失败，防止索引失去上游证据。
- contract check 不是 ready 会失败，防止未验证 receipt 被索引。
- CLI 在 `--require-index-ready` 下遇到失败报告会返回 1，同时仍生成诊断产物。

## 一句话总结

v985 把 receipt/check 从“两个可验证产物”推进成“一个可被后续治理链 lookup-only 消费的 receipt index”。

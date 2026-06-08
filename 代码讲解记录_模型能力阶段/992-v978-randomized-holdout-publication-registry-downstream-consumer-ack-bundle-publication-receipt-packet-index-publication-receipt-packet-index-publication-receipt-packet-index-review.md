# v978 randomized holdout publication receipt packet index review

## 目标与边界

v978 的目标是 review v977 的 `publication receipt packet index`。v977 已经把 packet 与 contract check 组合成 lookup-only index；v978 在 publication 前再做一层审核，确认 index 仍然可读、源 packet/check 仍然存在、source evidence 没有丢、lookup-only 使用边界没有漂移。

本版不训练模型，不改变 checkpoint，不证明模型能力提升，也不允许 promotion。`publish_ready=True` 只表示可以进入 lookup-only publication，不表示可用于生产推广。

## 前置路线

v978 接在 v977 后面：

- v975 构建 receipt packet。
- v976 复核 receipt packet contract。
- v977 把 packet/check 合成 receipt packet index。
- v978 review 这个 index，准备进入 publication。

这条路线仍然是“证据消费治理”，不是“模型质量升级”。它的价值在于让下游消费入口更可靠。

## 关键文件

- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review.py`
  - 核心 review builder。
  - 从 v977 index 中抽取 `summary`、`receipt_packet_index`、index rows、source packet rows 和 source evidence rows。
  - 运行 23 条检查后生成 `review`、`summary` 和 `interpretation`。
- `src/minigpt/randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - 本版采用短 artifact 文件名 `randomized_holdout_publication_receipt_packet_index_review_v978.*`，避免 Windows 长路径问题。
- `scripts/build_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review.py`
  - CLI 入口。
  - 支持目录输入，自动定位 v977 index JSON。
  - 支持 `--require-review-ready`、`--require-downstream-ready`、`--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review.py`
  - 覆盖 ready review、source evidence 缺失、lookup use 漂移、CLI 失败退出码、输出格式和 locator。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v978 review next step，指向 `publish_...publication_receipt_packet_index`。
- `src/minigpt/__init__.py`
  - 增加包级懒加载导出，保持与前序版本一致。

## 核心数据结构

### `review`

`review` 是本版的主对象，字段包括：

- `review_ready`：23 条检查全部通过时为 `True`。
- `review_id`：v978 review ID。
- `review_status`：`approved_for_downstream_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_publication`。
- `receipt_packet_index_path`：v977 index 路径。
- `receipt_packet_index_row_count`：应为 1。
- `source_packet_row_count`：应为 1。
- `source_evidence_count`：应为 2。
- `downstream_ready` / `publish_ready`：通过时为 `True`，仅用于 lookup-only publication。
- `lookup_ready` / `contract_check_ready`：来自 v977 index 的关键边界。
- `promotion_ready` / `approved_for_promotion`：固定为 `False`。
- `allowed_use`：固定为 `downstream_governance_lookup_only`。
- `blocked_uses`：继续保留 production promotion、quality expansion、training data claim expansion 等阻断项。

### `summary`

`summary` 是外部消费的轻量索引：

- `...publication_receipt_packet_index_review_ready=True`
- `review_status=approved_for_downstream_...publication`
- `receipt_packet_index_row_count=1`
- `source_packet_row_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `publish_ready=True`
- `promotion_ready=False`
- `passed_check_count=23`
- `failed_check_count=0`

## 23 条检查保护什么

本版检查分成几组：

1. 输入 index 文件必须存在，并且 v977 index 本身 `status=pass`。
2. index 的 decision 和 ready summary 必须与 v977 约定一致。
3. `lookup_scope` 与 `granted_use` 必须保持 downstream governance lookup only。
4. index 必须同时具备 `lookup_ready=True` 和 `contract_check_ready=True`。
5. index rows 必须只有一条，source packet rows 必须只有一条，lookup key 必须使用 `publication:` 命名空间。
6. index row 和 source packet row 都不能把 `promotion_ready` 置为 True。
7. source evidence 必须两条、均 pass、且文件路径仍然存在。
8. source packet 与 source packet check 文件必须仍然存在。
9. consumer boundary 和 model quality claim 必须保持 bounded。
10. source failed check count 必须为 0。
11. v977 的 next step 必须指向 v978 review。

这些检查让 publication 之前的审核不只是“读到一个 JSON”，而是确认 JSON 仍然与源证据、合同检查和使用边界一致。

## 路径长度维护修正

真实生成 v978 证据时，完整长链 artifact 文件名触碰了 Windows 路径长度边界。这里采取的做法是：

- 保留模块名和 Python 函数名，保证链路可追踪。
- 缩短 JSON/CSV/text/Markdown/HTML 文件名为 `randomized_holdout_publication_receipt_packet_index_review_v978.*`。
- 不改变 schema，不改变 CLI 输入方式，也不改变测试覆盖。

这也是后续版本应该借鉴的维护策略：长链模块名可以用于语义定位，但运行产物文件名不应无限增长。

## 运行证据

真实运行输入 v977 的 index 目录，输出在 `e/978/解释/publication-receipt-packet-index-publication-receipt-packet-index-publication-receipt-packet-index-review/`。

关键输出：

```text
status=pass
decision=randomized_holdout_publication_registry_downstream_consumer_ack_bundle_publication_receipt_packet_index_publication_receipt_packet_index_publication_receipt_packet_index_review_ready
failed_count=0
publish_ready=True
promotion_ready=False
passed_check_count=23
failed_check_count=0
```

Playwright MCP 截图保存在 `e/978/图片/`，页面展示 review boundary 和全部 check rows。

## 测试覆盖

本版测试覆盖：

- ready index 生成 ready review。
- source evidence 缺失会失败。
- `granted_use` 漂移为 production promotion 会失败。
- CLI 在 `--require-review-ready` 下遇到篡改 index 返回 `1`。
- 输出函数写出 JSON、CSV、text、Markdown、HTML。
- locator 能从目录输入找到默认 JSON。

测试重点是保护 publication 前的边界：source evidence 不能丢，lookup use 不能漂，promotion 不能被悄悄打开。

## 一句话总结

v978 在 publication 前复核 v977 index，并通过短 artifact 文件名修掉长路径风险，让后续 lookup-only publication 更稳。

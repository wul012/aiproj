# v981 publication index

## 目标与边界

v981 的目标是把 v979 lookup-only publication 和 v980 contract check 合成一个可查的 publication index。v980 已经证明 v979 publication 可以从 v978 review 重建；v981 负责把这个“通过检查的发布产物”放进下游 lookup index。

本版不做模型训练，不改 checkpoint，不做真实生产发布，也不扩展模型能力声明。它仍然是治理证据链的一环，边界是：

- `published_use=downstream_governance_lookup_only`
- `lookup_scope=downstream_governance_lookup_only`
- `promotion_ready=False`
- `approved_for_promotion=False`

## 前置路线

这一版接在 v979-v980 后面：

1. v979 发布 lookup-only publication。
2. v980 从 v978 review 重建 v979 publication，并通过 40 条字段一致性检查。
3. v981 读取 v979 和 v980，生成 publication index。

这条路线是“publication 可查化”，不是“模型能力扩大化”。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_index_v981.py`
  - 核心 index builder。
  - 输入 publication 与 publication check。
  - 校验发布状态、contract check、lookup-only use、源路径、行数、bounded claim、no-promotion 和 next step。
  - 输出 `publication_index`、`publication_index_rows`、`source_evidence_rows`、`summary` 和 `interpretation`。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_index_v981_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - 展示 lookup boundary、index row、source evidence 和检查表。
- `scripts/build_randomized_holdout_publication_receipt_packet_index_publication_index_v981.py`
  - CLI 入口。
  - 支持 publication/check 目录输入。
  - 支持 `--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_index_v981.py`
  - 覆盖通过路径、用途篡改、源 index 丢失、CLI 失败码和 artifact 渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增短 next step：`RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_PACKET_INDEX_PUBLICATION_INDEX_V981_NEXT_STEP`。
- `src/minigpt/__init__.py`
  - 增加短名 builder/writer 的懒加载导出。

## 核心数据结构

### `publication_index`

`publication_index` 是本版主产物：

- `index_ready`：25 条检查全部通过时为 `True`。
- `publication_index_id`：`randomized-holdout-publication-receipt-packet-index-publication-index-v981`。
- `lookup_scope`：固定为 `downstream_governance_lookup_only`。
- `lookup_key_count`：真实运行为 1。
- `publication_index_rows`：唯一 lookup row。
- `source_evidence_rows`：publication 与 publication_check 两条证据。
- `promotion_ready` / `approved_for_promotion`：固定为 `False`。

### `publication_index_rows`

每一行记录一个可查 publication：

- `lookup_key`
- `publication_id`
- `publication_status`
- `published_use`
- `source_publication_path`
- `source_publication_check_path`
- `source_review_path`
- `source_index_path`
- `contract_check_ready`
- `promotion_ready`

这让后续模块不用重新解析整条 v979/v980 证据链，也能定位 publication 和 check。

### `source_evidence_rows`

本版 source evidence 只有两条：

- `publication`
- `publication_check`

每条记录 path、SHA-256 和 pass/fail 状态。它们是最终证据的索引，不是临时文件。

## 25 条检查保护什么

检查重点分为五类：

1. v979 publication 文件和 v980 check 文件必须存在。
2. publication 必须 pass，decision 必须是 publication ready。
3. check 必须 pass，decision 必须是 contract check passed。
4. publication status、published use、row count、source packet row count 必须与 check 的 original/rebuilt 字段一致。
5. 源 review、源 index、源 packet、源 packet check 仍然存在，且 promotion 保持关闭。

这组检查保护的是“通过 contract check 的 publication 才能进入 index”，避免把篡改后的 publication 包装成可查入口。

## CLI 与输出

CLI 入口是：

```text
scripts/build_randomized_holdout_publication_receipt_packet_index_publication_index_v981.py
```

输入可以是 JSON 文件，也可以是输出目录。输出目录包含：

```text
randomized_holdout_publication_receipt_packet_index_publication_index_v981.json
randomized_holdout_publication_receipt_packet_index_publication_index_v981.csv
randomized_holdout_publication_receipt_packet_index_publication_index_v981.txt
randomized_holdout_publication_receipt_packet_index_publication_index_v981.md
randomized_holdout_publication_receipt_packet_index_publication_index_v981.html
```

`--require-index-ready` 和 `--require-lookup-ready` 用来把 CLI 变成发布门禁；`--require-promotion-ready` 仍会失败，因为这条链路不允许 promotion。

## 运行证据

真实运行输出在：

```text
e/981/解释/publication-index-v981/
```

关键结果：

```text
status=pass
index_ready=True
lookup_key_count=1
source_evidence_count=2
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/981/图片/v981-randomized-holdout-publication-receipt-packet-index-publication-index.png
```

## 一句话总结

v981 把通过 v980 contract check 的 v979 publication 纳入一个短名 lookup index，让后续 review 可以消费稳定索引，而不需要再追逐超长路径链。

# v988 publication receipt index receipt check

## 目标与边界

v988 的目标是给 v987 publication receipt index receipt 增加一层 contract check。v987 已经把 v986-reviewed receipt index 记录为 lookup-only downstream receipt；v988 负责证明这个 receipt artifact 可以从它记录的 v986 review 重新推导出来。

本版不训练模型，不修改 checkpoint，不改变 candidate/baseline 选择，也不把 lookup-only governance receipt 扩大成 production promotion。

## 前置路线

1. v985 将 v983 receipt 和 v984 receipt contract check 建成 receipt index。
2. v986 review receipt index，确认 source evidence、lookup-only 和 no-promotion 边界。
3. v987 记录 downstream consumer receipt。
4. v988 重新构造 v987 receipt 并比对原始 artifact。

v988 与 v984 的角色相近，都是“receipt contract check”。区别是 v984 检查 publication receipt，v988 检查 receipt index receipt。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.py`
  - 核心 contract check builder。
  - 定位 v987 receipt JSON，读取 receipt 内的 source v986 review path，重建 v987 receipt，并比较关键字段。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - HTML 用于 Playwright MCP 截图和人工审阅。
- `scripts/check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v988.py`
  - CLI 入口。
  - 支持 `--require-pass` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988.py`
  - 覆盖正常重建、字段篡改、source review 缺失、CLI 失败码和输出渲染。

## 核心数据结构

v988 输出的 `summary` 不是模型指标，而是 contract check 摘要：

- `contract_check_ready`
  - 所有检查通过时为 `True`。
- `source_receipt_index_review`
  - receipt 中记录的 v986 review JSON 路径。
- `original_receipt_status` / `rebuilt_receipt_status`
  - 原始 receipt 与重建 receipt 的状态。
- `original_granted_use` / `rebuilt_granted_use`
  - 用于确认仍是 `downstream_governance_lookup_only`。
- `original_lookup_key_count` / `rebuilt_lookup_key_count`
  - 用于确认 lookup key 数量没有漂移。
- `original_promotion_ready` / `rebuilt_promotion_ready`
  - 用于确认 promotion 仍关闭。
- `next_step`
  - 通过后指向 `index_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_v988`。

原始 receipt 和重建 receipt 会分别保存在：

- `original_summary`
- `rebuilt_summary`
- `original_receipt`
- `rebuilt_receipt`

这些字段是最终证据的一部分，也方便后续版本继续消费。

## 核心函数

`locate_receipt_v988()`：

- 如果输入是目录，就补齐 v987 JSON 文件名。
- 如果输入是 JSON 文件，则直接使用。

`build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_check_v988()`：

1. 读取原始 v987 receipt 的 summary 和 receipt body。
2. 从 `receipt_index_review_path` 找到 source v986 review。
3. 调用 v987 builder 重建 receipt。
4. 比较顶层 `status`、`decision`、`failed_count`。
5. 比较 `consumer_receipts`。
6. 比较 summary 和 receipt body 的关键字段。
7. 生成 `issues`、`check_rows`、`summary` 和 `interpretation`。

`resolve_exit_code()`：

- 在 `--require-pass` 下，如果 contract check 不通过就返回 `1`。
- receipt 本身仍是 lookup-only、promotion blocked，这不会导致 check 失败。

## 字段比对范围

summary 比对包含：

```text
ready flag
receipt id/type/status
consumer name
granted use
receipt index row count
source evidence count
lookup key count
promotion flags
consumer boundary
blocked uses
next step
check counts
```

receipt body 比对包含：

```text
receipt ready/id/type/status
consumer name
requested/granted use
source review path
row/evidence counts
lookup keys
review id/status
blocked uses
promotion flags
consumer boundary
model quality claim
source receipt/check paths
next step
```

这让 v988 能抓到 artifact 被篡改、source review 丢失、用途扩大、promotion 字段打开、consumer receipt 漂移等问题。

## 输入输出流程

CLI 流程：

```text
receipt dir/json
 -> locate_receipt_v988
 -> read_json_report
 -> build contract check
 -> write json/csv/txt/md/html
 -> resolve_exit_code
```

JSON 是后续版本的主输入；CSV 记录逐项 check rows；text 用于命令行快速核对；Markdown/HTML 用于人工审阅和截图归档。

## 测试覆盖

测试保护了五类行为：

- ready receipt 可以从 source review 重建，并得到 `status=pass`。
- 篡改 `granted_use` 会同时触发 summary 和 receipt body 的失败项。
- 删除或改错 `receipt_index_review_path` 会触发 source review 缺失失败。
- CLI 在 `--require-pass` 下遇到失败 check 返回 `1`。
- artifact writer 能生成 JSON、CSV、text、Markdown、HTML，渲染文本包含关键状态。

这些断言覆盖的是完整链路，不只是函数返回值：测试会先构造 v986 review，再生成 v987 receipt，最后检查 v988 contract check。

## 运行证据

真实运行证据写入：

```text
e/988/解释/publication-receipt-index-receipt-check-v988/
```

核心结果：

```text
status=pass
contract_check_ready=True
original_receipt_status=publication_receipt_index_lookup_receipted
rebuilt_receipt_status=publication_receipt_index_lookup_receipted
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=42
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/988/图片/v988-randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-check.png
```

## 一句话总结

v988 把 v987 的 lookup-only receipt 从“已经记录”推进到“能从源 review 重新推导并可审计”，进一步压住 receipt artifact 漂移和用途扩大风险。

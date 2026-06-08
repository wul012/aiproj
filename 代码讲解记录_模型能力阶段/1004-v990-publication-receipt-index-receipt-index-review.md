# v990 publication receipt index receipt index review

## 目标与边界

v990 的目标是 review v989 的 receipt index，判断它是否可以进入 lookup-only publication flow。v989 已经把 v987 receipt 和 v988 check 收成 digest-backed index；v990 负责在发布前复核这个 index 的路径、digest、lookup namespace 和 no-promotion 边界。

本版不训练模型，不更新 checkpoint，不改变模型质量结论，也不批准 production promotion。

## 前置路线

1. v987 记录 receipt index 的下游 receipt。
2. v988 检查 v987 receipt 可从 v986 review 重建。
3. v989 将 v987/v988 收成 receipt index。
4. v990 review 这个 receipt index，准备进入 lookup-only publication。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990.py`
  - 核心 review builder。
  - 读取 v989 index，校验 index row、source evidence、digest、source files 和 no-promotion 边界。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
- `scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v990.py`
  - CLI 入口，支持 ready/promotion exit-code gate。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_review_v990.py`
  - 覆盖 ready review、bad digest、lookup scope 篡改、source receipt 缺失、CLI 失败码和输出渲染。

## 核心数据结构

`review` 是 v990 的核心输出：

- `review_ready`
  - 所有检查通过时为 `True`。
- `review_id`
  - 固定为 `randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-review-v990`。
- `review_status`
  - ready 时为 `approved_for_publication_receipt_index_receipt_index_publication_lookup_only`。
- `receipt_index_path`
  - 指向 v989 index JSON。
- `receipt_index_row_count`
  - 必须为 1。
- `source_evidence_count`
  - 必须为 2。
- `lookup_keys`
  - 必须使用 `receipt-index-receipt:` 命名空间。
- `receipt_ready` / `lookup_ready` / `contract_check_ready`
  - 三个 gate 都必须为 `True`。
- `promotion_ready`
  - 固定为 `False`。
- `next_step`
  - 指向 `publish_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v990`。

## 核心检查

v990 的 `_checks()` 覆盖：

- receipt index 文件存在。
- v989 index 顶层 status 和 decision ready。
- summary 和 body 的 ready flag 一致。
- lookup scope 和 granted use 都是 downstream lookup only。
- lookup ready 和 contract check ready 都为真。
- receipt index row 正好一条。
- lookup key 使用 `receipt-index-receipt:` 命名空间。
- index row 不允许 promotion。
- source evidence 正好两条且 status pass。
- source evidence SHA-256 格式有效。
- source evidence path 实际存在。
- source receipt、source check、source review、prior receipt、prior check 都存在。
- consumer boundary 和 model quality claim 不扩大。
- promotion flags 全部为 `False`。
- source failed check count 为 0。
- source next step 指向 v990 review。

## 输入输出流程

CLI 流程：

```text
v989 index dir/json
 -> locate_receipt_index_v990
 -> read_json_report
 -> build review
 -> write json/csv/txt/md/html
 -> resolve_exit_code
```

JSON 是后续 publication 的主输入；CSV 记录逐项 review check；HTML 用于截图和人工审阅。

## 测试覆盖

测试保护五类风险：

- ready v989 index 可以被 review。
- SHA-256 被篡改时失败。
- lookup scope 被改成 promotion 用途时失败。
- source receipt 路径丢失时失败。
- CLI 在 `--require-review-ready` 下会返回失败码。

测试 fixture 从 v989 的 ready index 构建，覆盖 v987-v990 的连续链路。

## 运行证据

真实运行证据：

```text
e/990/解释/publication-receipt-index-receipt-index-review-v990/
```

关键结果：

```text
status=pass
review_ready=True
lookup_key_count=1
source_evidence_count=2
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

Playwright MCP 截图：

```text
e/990/图片/v990-randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-review.png
```

## 一句话总结

v990 把 v989 的 receipt index 从“已建立”推进到“发布前已审阅”，确认它只能进入 lookup-only publication，不能被误用为生产晋升依据。

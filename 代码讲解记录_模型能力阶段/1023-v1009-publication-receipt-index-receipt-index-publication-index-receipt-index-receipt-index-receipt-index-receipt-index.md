# v1009 publication receipt index receipt index publication index receipt index receipt index receipt index receipt index

## 目标与边界

v1009 的目标是把 v1007 lookup-only receipt 和 v1008 receipt contract check 合并成下一层 receipt index。v1007 说明“下游 lookup-only consumer 已 receipt”，v1008 说明“这份 receipt 能从源 v1006 review 重建”。v1009 把两者变成一个 digest-backed index，方便 v1010 做 review。

本版不训练模型，不生成 checkpoint，不扩大模型质量声明，不改变 promotion 结论，也不新开治理链。它只把已有 receipt 与 check 收成结构化索引。

## 前置路线

1. v1006 review v1005 receipt index。
2. v1007 根据 v1006 review 记录 lookup-only downstream receipt。
3. v1008 从 v1006 review 重建 v1007 receipt，确认 contract check pass。
4. v1009 合并 v1007 和 v1008，生成下一步可 review 的 receipt index。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_v1009.py`
  - 核心 index builder。
  - 负责读取 receipt/check、执行 24 条检查、生成 receipt index row 与 source evidence rows。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_v1009_artifacts.py`
  - 负责 JSON、CSV、TXT、Markdown、HTML 输出。
- `scripts/build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_v1009.py`
  - CLI 入口，支持 `--receipt`、`--receipt-check`、`--require-index-ready`、`--require-lookup-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_receipt_index_v1009.py`
  - 覆盖 ready 路径、granted use 篡改、contract check 未 ready、CLI 与输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1009 pass 后的 review 路由常量。

## 核心数据结构

`receipt_index` 是 v1009 的核心结构：

- `index_ready`
  - 只有 receipt 与 check 都通过时为 `True`。
- `receipt_index_id`
  - 固定为 `randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-index-receipt-index-receipt-index-v1009`。
- `lookup_scope`
  - 固定为 `downstream_governance_lookup_only`。
- `receipt_index_rows`
  - 保存 lookup key、receipt id、receipt status、granted use、source receipt/check/review/index 路径。
- `source_evidence_rows`
  - 对 v1007 receipt 和 v1008 receipt check 计算 SHA-256。
- `promotion_ready`
  - 固定为 `False`。

## 核心检查

v1009 的 `_checks()` 保护以下边界：

- v1007 receipt 文件必须存在。
- v1008 receipt contract check 文件必须存在。
- receipt 顶层 status/decision 必须 ready。
- receipt summary 与 receipt body 必须 ready。
- receipt status 必须是 lookup-only receipted。
- receipt check 顶层 status/decision 必须通过。
- `contract_check_ready=True`。
- receipt status 必须和 v1008 original/rebuilt status 一致。
- granted use 必须在 receipt summary、receipt body、original check、rebuilt check 中全部保持 lookup-only。
- lookup key count 必须为 1。
- source evidence count 必须为 2。
- source review/index/receipt/check 路径必须仍存在。
- consumer boundary 与 model quality claim 不能扩大。
- promotion 与 approved_for_promotion 必须保持 `False`。
- source receipt/check failed count 必须为 0。
- next step 必须从 receipt -> check -> index 正常衔接。

## 输入输出流程

CLI 流程：

```text
--receipt -> locate_receipt_v1009 -> read_json_report
--receipt-check -> locate_receipt_check_v1009 -> read_json_report
-> build_*_v1009
-> write_*_outputs
-> resolve_exit_code
```

真实输出目录：

```text
e/1009/解释/receipt-index-v1009/
```

该目录下的 JSON、CSV、TXT、Markdown、HTML 都是最终证据。JSON 会作为 v1010 review 的输入；CSV 展开 index row；HTML 用于截图。

## 测试覆盖

focused 测试覆盖：

- 合法 receipt + check 可以生成 ready index。
- 篡改 `granted_use` 会失败。
- 关闭 `contract_check_ready` 会失败。
- CLI 能定位目录输入、写出 sidecar，并在 require-ready 下返回正确退出码。

## 运行证据

归档说明：

```text
e/1009/解释/说明.md
```

HTML 截图：

```text
e/1009/图片/v1009-receipt-index.png
```

真实运行摘要：

```text
status=pass
index_ready=True
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=24
failed_check_count=0
```

## 一句话总结

v1009 把 v1007 receipt 和 v1008 contract check 收成可 review 的 lookup-only receipt index，继续保持 digest-backed、no-promotion 的证据链。

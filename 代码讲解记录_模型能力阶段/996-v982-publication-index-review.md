# v982 publication index review

## 目标与边界

v982 的目标是审查 v981 publication index 是否可以进入 receipt flow。v981 已经把 v979 publication 与 v980 contract check 合成 lookup index；v982 负责确认这个 index 仍然可查、可追溯、未越权。

本版不做模型训练，不改 checkpoint，不做线上发布，也不扩展模型质量声明。它只回答一个问题：v981 index 是否可以被后续 receipt 消费。

## 前置路线

这一版接在 v981 后面：

1. v979 生成 lookup-only publication。
2. v980 contract check 证明 publication 可从源 review 重建。
3. v981 把 publication 和 check 合成 publication index。
4. v982 review 这个 index，确认可以进入 receipt。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_index_review_v982.py`
  - 核心 review builder。
  - 读取 v981 index。
  - 校验 index status、summary/body ready、lookup scope、published use、index row、source evidence、digest、源文件、bounded claim、no-promotion 和 next step。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_index_review_v982_artifacts.py`
  - 输出 JSON、CSV、text、Markdown、HTML。
  - HTML 展示 review boundary 和 22 条检查。
- `scripts/review_randomized_holdout_publication_receipt_packet_index_publication_index_v982.py`
  - CLI 入口。
  - 支持 index JSON 或目录输入。
  - 支持 `--require-review-ready` 和 `--require-receipt-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_index_review_v982.py`
  - 覆盖 ready review、坏 SHA-256、lookup scope 漂移、CLI 失败码和输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增短 next step：`record_randomized_holdout_publication_receipt_packet_index_publication_receipt_v982`。
- `src/minigpt/__init__.py`
  - 增加短名 builder/writer 的懒加载导出。

## 核心数据结构

### `review`

`review` 是本版主产物：

- `review_ready`：22 条检查全部通过时为 `True`。
- `review_id`：`randomized-holdout-publication-receipt-packet-index-publication-index-review-v982`。
- `review_status`：`approved_for_publication_index_receipt_lookup_only`。
- `publication_index_path`：v981 index 路径。
- `publication_index_row_count=1`。
- `source_evidence_count=2`。
- `receipt_ready=True`。
- `promotion_ready=False`。
- `next_step=record_randomized_holdout_publication_receipt_packet_index_publication_receipt_v982`。

### `source_evidence_rows`

v982 不重新生成 source evidence，而是审查 v981 的两条 evidence：

- `publication`
- `publication_check`

它要求每条 evidence 都是 pass，路径存在，SHA-256 是 64 位十六进制摘要。

## 22 条检查保护什么

检查重点是防止 index 变成不可追溯的入口：

1. v981 index 文件存在。
2. index status 和 decision ready。
3. summary 与 body 都 ready。
4. lookup scope 与 published use 仍为 downstream lookup only。
5. lookup/contract ready 仍为 True。
6. index row 恰好 1 条，lookup key 使用 `publication-index:` namespace。
7. source evidence 恰好 2 条，且 pass、digest 合法、文件存在。
8. source publication 与 source check 文件仍存在。
9. consumer boundary 与 model quality claim 仍 bounded。
10. promotion 仍关闭。
11. source failed check count 为 0。
12. next step 必须从 v981 index 指向 v982 review。

## 测试覆盖

测试覆盖了真实 ready 路径，也覆盖了两类典型坏输入：

- SHA-256 被篡改为 `bad`，`source_evidence_digests` 会失败。
- `lookup_scope` 被改为 `production_promotion`，`lookup_scope_downstream` 会失败。

CLI 测试确认 `--require-review-ready` 在坏 index 上返回 1，并且仍会写出失败证据。

## 运行证据

真实运行输出在：

```text
e/982/解释/publication-index-review-v982/
```

关键结果：

```text
status=pass
review_ready=True
receipt_ready=True
lookup_key_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=22
failed_check_count=0
```

Playwright MCP 截图保存到：

```text
e/982/图片/v982-randomized-holdout-publication-receipt-packet-index-publication-index-review.png
```

## 一句话总结

v982 把 v981 publication index 从“已生成的 lookup index”推进为“通过 review、可进入 receipt 的 lookup-only index”。

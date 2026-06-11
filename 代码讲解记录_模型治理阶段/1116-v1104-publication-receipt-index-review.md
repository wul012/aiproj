# v1104 publication receipt index review

本版目标是审核 v1103 receipt index，确认它可以进入下一轮 lookup-only receipt recording。

它不训练模型，不接受 candidate，不修改 v1103 index，不生成 receipt，也不放开 production promotion。它只是把“index 已生成”推进为“index 已通过 review，可以被下一步 receipt 记录消费”。

## 入口

本版入口是 CLI：

```text
scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1104.py
```

核心模块是：

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1104.py
```

CLI 输入 v1103 index 目录或 JSON 文件，输出 JSON/CSV/TXT/Markdown/HTML sidecar。`--require-review-ready` 和 `--require-lookup-ready` 会把 review 或 lookup 失败转成非零退出码。

## 输出模型

最外层 report 包含：

```text
status
decision
failed_count
summary
review
source_receipt_index_summary
source_receipt_index
receipt_index_rows
source_evidence_rows
check_rows
outputs
```

关键边界字段是：

```text
review_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
```

`promotion_ready=False` 是硬边界：v1104 只允许进入 lookup-only receipt recording，不允许生产发布。

## 上游证据

本版读取真实上游证据：

```text
f/1103/解释/receipt-index-v1103
```

v1103 index 由 v1101 receipt 和 v1102 contract check 组成，包含两份 source evidence digest。v1104 不重写这些上游证据，只审查它们是否仍然可被下一步消费。

## 核心流程

1. CLI 定位 v1103 index JSON。
2. builder 读取 index report、summary、index body、receipt index rows 和 source evidence rows。
3. `_checks` 验证 v1103 decision、ready key、lookup scope、granted use、source evidence 数量、source 文件存在、contract check ready 和 no-promotion boundary。
4. `_review` 在全部检查通过后生成 review body，并把下一步路由到 v1104 receipt recording。
5. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
6. Playwright MCP 打开 HTML sidecar 并保存截图到 `f/1104/图片`。

## 关键检查

- `receipt_index_passed`：保护上游 index 已成功生成。
- `receipt_index_decision_ready`：保护 source decision 是 v1103 ready。
- `lookup_scope_downstream` 和 `granted_use_lookup_only`：保护只读消费边界。
- `source_receipt_file_exists` 和 `source_receipt_check_file_exists`：保护 receipt/check 路径仍可追踪。
- `contract_check_ready`：保护 receipt 先经过重建式 contract check。
- `promotion_still_false`：保护 review 不越权成 production promotion。
- `source_next_step_matches`：保护 v1103 index 的下一步确实指向 review。

## 测试覆盖

专项测试覆盖：

- 合法 v1103 index 可以通过 review。
- 篡改 lookup scope 会失败，保护下游只读边界。
- 删除 source path 会失败，保护证据可追溯。
- 把 promotion 打开会失败，保护本阶段不越权。
- CLI 能输出 sidecar，并把 require gate 接到退出码。

这些测试让 v1104 成为 receipt recording 前的审查层，而不是简单展示层。

## 运行证据

真实命令消费 `f/1103/解释/receipt-index-v1103`，输出确认：

- `status=pass`
- `review_ready=True`
- `receipt_index_row_count=1`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=22`
- `failed_check_count=0`

验证侧跑了 focused v1104 tests（`5 passed in 0.41s`）、py_compile、source hygiene（`2271/2271 clean`）、`git diff --check` 和真实 CLI。Playwright MCP 页面快照确认 HTML 中存在 `Review Summary`、`Receipt Index Rows`、`Source Evidence` 和 `Checks`，截图保存为 `f/1104/图片/v1104-receipt-index-review.png`。

## 链路角色

v1104 位于这一轮链路的 review 位置：

```text
v1101 receipt -> v1102 contract check -> v1103 index -> v1104 review
```

下一步是 record receipt，不是 promotion。

## 一句话总结

v1104 把 v1103 receipt index 从“可查”推进为“经过 review、可进入下一步 lookup-only receipt recording”的治理证据。

# v1100 publication receipt index review

本版目标是审核 v1097 生成的 digest-backed receipt index，确认它可以进入下一步 lookup-only receipt recording。

它不训练模型，不接受 candidate，不修改 v1097 index，不生成 receipt，也不放开 production promotion。它只是把“index 可以生成”推进为“index 已经通过 review，可以被下一步 receipt 记录消费”。

## 入口

本版入口是 CLI：

```text
scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1100.py
```

核心模块是：

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1100.py
```

CLI 输入 v1097 index 目录或 JSON 文件，输出 JSON/CSV/TXT/Markdown/HTML sidecar。`--require-review-ready` 和 `--require-lookup-ready` 会把 review 或 lookup 失败转成非零退出码。

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

其中 `promotion_ready=False` 是硬边界：v1100 只允许进入 lookup-only receipt recording，不允许生产发布。

## 上游证据

本版读取真实上游证据：

```text
e/1097/解释/receipt-index-v1097
```

v1097 index 本身由 v1095 receipt 和 v1096 contract check 组成，包含两份 source evidence digest。v1100 不重写这些上游证据，只审查它们是否仍然可被下一步消费。

## 核心流程

1. CLI 定位 v1097 index JSON。
2. builder 读取 index report、summary、index body、receipt index rows 和 source evidence rows。
3. `_checks` 验证 v1097 decision、ready key、lookup scope、granted use、source evidence 数量、source 文件存在、contract check ready 和 no-promotion boundary。
4. `_review` 在全部检查通过后生成 review body，并把下一步路由到 v1100 receipt recording。
5. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
6. Playwright MCP 打开 HTML sidecar 并保存截图到 `f/1100/图片`。

## 关键检查

- `receipt_index_passed`：保护上游 index 已成功生成。
- `receipt_index_decision_ready`：保护 source decision 是 v1097 ready。
- `lookup_scope_downstream` 和 `granted_use_lookup_only`：保护只读消费边界。
- `source_receipt_file_exists` 和 `source_receipt_check_file_exists`：保护 receipt/check 路径仍可追踪。
- `contract_check_ready`：保护 receipt 先经过重建式 contract check。
- `promotion_still_false`：保护 review 不越权成 production promotion。
- `source_next_step_matches`：保护 v1097 index 的下一步确实指向 review。

## 测试覆盖

专项测试覆盖：

- 合法 v1097 index 可以通过 review。
- 篡改 lookup scope 会失败，保护下游只读边界。
- 删除 source path 会失败，保护证据可追溯。
- 把 promotion 打开会失败，保护本阶段不越权。
- CLI 能输出 sidecar，并把 require gate 接到退出码。

这些测试让 v1100 成为 receipt recording 前的审查层，而不是简单展示层。

## 运行证据

真实命令消费 `e/1097/解释/receipt-index-v1097`，输出确认：

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

验证侧还跑了 focused v1100 tests（`5 passed in 0.58s`）、py_compile、source hygiene（`2255/2255 clean`）和 `git diff --check`。这些检查分别保护代码可加载、测试链路可复现、源码无 BOM/语法问题，以及提交前没有空白差异风险。

Playwright MCP 页面快照确认 HTML 中存在 `Review Summary`、`Receipt Index Rows`、`Source Evidence` 和 `Checks`，截图保存为 `f/1100/图片/v1100-receipt-index-review.png`。

## 链路角色

v1100 位于这一轮链路的 review 位置：

```text
v1095 receipt -> v1096 contract check -> v1097 index -> v1100 review
```

下一步是 record receipt，不是 promotion。

## 一句话总结

v1100 把 v1097 digest-backed index 从“可查”推进为“经过 review、可进入下一步 lookup-only receipt recording”的治理证据。

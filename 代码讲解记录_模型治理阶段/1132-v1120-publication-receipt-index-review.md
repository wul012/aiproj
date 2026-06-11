# v1120 publication receipt index review

## 本版目标与边界

v1120 的目标是审阅 v1119 receipt index，确认它可以被下一步 receipt recording 安全消费。它检查 index 是否通过、lookup row 是否稳定、source evidence 是否仍然完整、contract check 是否 ready，以及 production promotion 边界是否继续关闭。

本版不训练模型，不修改 v1119 index，不扩大 candidate 的能力声明。`review_ready=True` 只表示这份 index 可以被记录为下一份 lookup-only receipt，不表示模型质量提升或生产放行。

## 前置路线

v1120 承接：

```text
v1117 receipt -> v1118 contract check -> v1119 index -> v1120 review
```

v1119 已经把 v1117 receipt 和 v1118 contract check 合成一份 downstream lookup index。v1120 的职责是给这份 index 增加准入审阅，避免下一步 receipt recording 继承错误路径、错误用途或错误 promotion 解释。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1120.py
```

核心 review builder。它读取 v1119 index JSON，抽取 source receipt index summary、receipt index rows、source evidence rows 和 check rows，生成审阅对象、检查结果、summary 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1120_artifacts.py
```

artifact writer。它把同一份 report 输出为 JSON、CSV、TXT、Markdown 和 HTML。JSON 是 v1121 的机器输入，Markdown/HTML 是审阅和归档页面。

```text
scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1120.py
```

CLI 入口。`--require-review-ready` 会要求 review 通过，`--require-lookup-ready` 会要求 lookup side 仍可用。

## 输入、输出与核心流程

真实输入：

```text
f/1119/解释/receipt-index-v1119
```

真实输出：

```text
f/1120/解释/receipt-index-review-v1120
```

核心流程是：定位 v1119 index JSON，读取 index summary、receipt index rows、source evidence 和 check rows，验证 lookup-only scope、contract check readiness、source paths、source evidence digest 和 no-promotion，最后输出 JSON/CSV/TXT/Markdown/HTML。

`summary` 给后续 receipt recording 读取：

```text
review_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
next_step=record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1120
```

## 关键检查

- `receipt_index_file_exists`：保护输入 JSON 路径没有丢失。
- `receipt_index_passed`：保护 v1119 index 本身是 pass。
- `index_ready`：保护 index 不是半成品。
- `lookup_scope_matches`：保护用途仍是 `downstream_governance_lookup_only`。
- `receipt_index_row_count_is_one`：保护 lookup row 数量稳定。
- `lookup_key_count_is_one`：保护 lookup key 不丢失、不膨胀。
- `source_evidence_count_is_two`：保护 receipt 与 contract check 证据都在。
- `contract_check_ready`：保护 v1118 check 被纳入审阅。
- `promotion_ready_false`：保护审阅不会被误读为 production promotion。

## 测试覆盖

focused tests 覆盖合法 v1119 index、granted use 篡改、source evidence digest 缺失、source path 漂移、CLI gating 和 artifact 输出。测试保护的是 review 的准入语义：ready 才能进入 receipt recording，promotion 仍然不打开。

## 运行证据

真实 CLI 输出：

```text
status=pass
review_ready=True
receipt_index_row_count=1
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=22
failed_check_count=0
```

验证包括 py_compile、focused v1120 tests（`5 passed in 0.63s`）、source hygiene（`2335/2335 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1120/图片/v1120-receipt-index-review.png
```

## 链路角色

v1120 位于 index 之后、receipt recording 之前。它把 v1119 index 从“可查找”推进为“已审阅、可被记录为下一份 lookup-only receipt”，同时继续阻断任何 production promotion 解释。

## 一句话总结

v1120 给 v1119 receipt index 增加了可阻断的审阅层，让下一份 lookup-only receipt recording 有清晰、可复核的准入证据。

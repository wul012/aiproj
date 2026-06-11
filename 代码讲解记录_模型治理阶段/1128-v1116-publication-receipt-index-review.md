# v1116 publication receipt index review

## 本版目标与边界

v1116 的目标是审阅 v1115 receipt index，确认它可以被下一步 receipt recording 安全消费。它检查 index 是否通过、lookup row 是否稳定、source evidence 是否仍然完整、contract check 是否 ready，以及 production promotion 边界是否继续关闭。

本版不训练模型，不修改 v1115 index，不扩大 candidate 的能力声明。`review_ready=True` 只表示这份 index 可以被记录为下一份 lookup-only receipt，不表示模型质量提升或生产放行。

## 前置路线

v1116 承接：

```text
v1113 receipt -> v1114 contract check -> v1115 index -> v1116 review
```

v1115 已经把 v1113 receipt 和 v1114 contract check 合成一份 downstream lookup index。v1116 的职责是给这份 index 增加准入审阅，避免下一步 receipt recording 继承错误路径、错误用途或错误 promotion 解释。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1116.py
```

核心 review builder。它读取 v1115 index JSON，抽取 source receipt index summary、receipt index rows、source evidence rows 和 check rows，生成审阅对象、检查结果、summary 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1116_artifacts.py
```

artifact writer。它把同一份 report 输出为 JSON、CSV、TXT、Markdown 和 HTML。JSON 是 v1117 的机器输入，Markdown/HTML 是审阅和归档页面。

```text
scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1116.py
```

CLI 入口。`--require-review-ready` 会要求 review 通过，`--require-lookup-ready` 会要求 lookup side 仍可用。`--require-promotion-ready` 保留为显式阻断选项，本链路不应启用，因为 promotion 应保持关闭。

```text
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1116.py
```

专项测试。它覆盖合法审阅、granted use 篡改、source evidence digest 缺失、source path 漂移、CLI gating 和 artifact 输出。

## 输入与输出

真实输入：

```text
f/1115/解释/receipt-index-v1115
```

真实输出：

```text
f/1116/解释/receipt-index-review-v1116
```

输出 report 的关键字段包括：

```text
status
decision
failed_count
issues
receipt_index_path
source_receipt_index_summary
source_receipt_index
receipt_index_rows
source_evidence_rows
check_rows
summary
interpretation
```

其中 `summary` 是后续 receipt recording 最重要的读取面：

```text
review_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
next_step=record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1116
```

## 核心流程

1. CLI 接收 v1115 index 输出目录，定位其中的 JSON report。
2. builder 读取 JSON，确认上游 `status=pass` 且 index ready。
3. builder 抽取单条 receipt index row，并保留 source receipt、source receipt check、source review、source receipt index 四类路径。
4. builder 读取两条 source evidence row，保留 kind、path、sha256 和 status。
5. `_checks` 逐项验证 index 状态、lookup scope、lookup key 数量、source evidence 数量、contract check readiness 和 promotion boundary。
6. artifact writer 写出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML，确认 `Review Summary`、`Receipt Index Rows`、`Source Evidence` 和 `Checks` 可见，然后保存截图。

## 关键检查

- `receipt_index_file_exists`：保护输入 JSON 路径没有丢失。
- `receipt_index_passed`：保护 v1115 index 本身是 pass。
- `index_ready`：保护 index 不是半成品。
- `lookup_scope_matches`：保护用途仍是 `downstream_governance_lookup_only`。
- `receipt_index_row_count_is_one`：保护 lookup row 数量稳定。
- `lookup_key_count_is_one`：保护 lookup key 不丢失、不膨胀。
- `source_evidence_count_is_two`：保护 receipt 与 contract check 证据都在。
- `source_receipt_path_exists` 和 `source_receipt_check_path_exists`：保护 source artifact 仍然可追溯。
- `contract_check_ready`：保护 v1114 check 被纳入审阅。
- `promotion_ready_false`：保护审阅不会被误读为 production promotion。

这些检查让 v1116 成为下一次 receipt recording 的准入门，而不是普通展示页。

## 测试覆盖

focused tests 覆盖：

- 合法 v1115 index 可以生成 ready review。
- 篡改 `granted_use` 会失败，防止 lookup-only 用途漂移。
- 删除 source evidence digest 会失败，防止证据行变成不可校验引用。
- 篡改 source path 会失败，防止下游记录错误来源。
- CLI 在 `--require-review-ready` 和 `--require-lookup-ready` 下能把失败结果转成非零退出码。
- artifact writer 会生成 JSON/CSV/TXT/Markdown/HTML。

测试保护的是 review 的准入语义：ready 才能进入 receipt recording，promotion 仍然不打开。

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

验证包括 py_compile、focused v1116 tests（`5 passed in 0.53s`）、source hygiene（`2319/2319 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1116/图片/v1116-receipt-index-review.png
```

## 链路角色

v1116 位于 index 之后、receipt recording 之前。它把 v1115 index 从“可查找”推进为“已审阅、可被记录为下一份 lookup-only receipt”，同时继续阻断任何 production promotion 解释。

## 一句话总结

v1116 给 v1115 receipt index 增加了可阻断的审阅层，让下一份 lookup-only receipt recording 有清晰、可复核的准入证据。

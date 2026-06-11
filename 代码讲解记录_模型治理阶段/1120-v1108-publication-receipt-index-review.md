# v1108 publication receipt index review

## 本版目标与边界

v1108 的目标是审阅 v1107 receipt index，确认这份 index 能进入下一步 lookup-only receipt recording。它检查 index 是否 ready、lookup row 是否稳定、source evidence 是否完整、contract check 是否存在且通过，以及 promotion 边界是否仍然关闭。

本版不训练模型，不修改 v1107 index，不生成新的模型质量结论。`review_ready=True` 只表示治理索引可以被记录成下一份 receipt，不表示 candidate 可以进入生产。

## 前置路线

v1108 承接：

```text
v1105 receipt -> v1106 contract check -> v1107 index -> v1108 review
```

v1107 已把 receipt 和 check 合并成 lookup-only index。v1108 的职责是给下一步 receipt recording 增加人工/机器可读的审阅层，防止 index 在进入 receipt 前出现路径、用途或 no-promotion 漂移。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1108.py
```

核心 review builder，读取 v1107 index report，生成 review summary、review rows、checks 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1108_artifacts.py
```

artifact writer，输出 JSON、CSV、TXT、Markdown、HTML。JSON 给 v1109 receipt recording 消费，HTML/Markdown 给人工审阅。

```text
scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1108.py
```

CLI 入口。`--require-review-ready` 和 `--require-lookup-ready` 会把审阅失败转成非零退出码；`--require-promotion-ready` 仍然不应在本链路使用，因为 promotion 应保持关闭。

```text
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1108.py
```

专项测试覆盖合法 review、lookup scope 篡改、缺失 source evidence、CLI gating 和 artifact 输出。

## 输入与输出

真实输入：

```text
f/1107/解释/receipt-index-v1107
```

真实输出：

```text
f/1108/解释/receipt-index-review-v1108
```

输出 report 的关键字段包括：

```text
status
decision
failed_count
review
source_receipt_index
check_rows
summary
interpretation
```

`summary` 是后续 v1109 最关心的读取面：

```text
review_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
next_step=record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1108
```

## 核心流程

1. CLI 定位 v1107 index JSON。
2. builder 读取 index report、receipt index rows、source evidence 和 summary。
3. review builder 生成审阅对象，保存 review status、approved use 和 next step。
4. `_checks` 验证 index pass、lookup row 数量、lookup key 数量、source evidence 数量、contract check readiness 和 promotion boundary。
5. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
6. Playwright MCP 打开 HTML，确认 `Review Summary`、`Receipt Index Rows`、`Source Evidence`、`Checks` 可见并截图。

## 关键检查

- `receipt_index_passed`：保护 v1107 index 本身是 pass。
- `index_ready`：保护 index 不是半成品。
- `lookup_scope_matches`：保护用途仍是 `downstream_governance_lookup_only`。
- `receipt_index_row_count_is_one`：保护 index 只有一条 lookup row。
- `lookup_key_count_is_one`：保护 lookup key 不丢失、不膨胀。
- `source_evidence_count_is_two`：保护 receipt 与 contract check 两类证据都保留。
- `contract_check_ready`：保护 v1106 check 被纳入审阅。
- `promotion_ready_false`：保护 review 不会打开生产 promotion。

这些检查让 review 成为下一次 receipt recording 的准入门，而不是普通摘要。

## 测试覆盖

focused tests 覆盖：

- 合法 v1107 index 可以生成 ready review。
- 篡改 lookup scope 会失败。
- 缺失 source evidence 会失败。
- CLI `--require-review-ready` 和 `--require-lookup-ready` 能阻断失败结果。
- artifact writer 生成 JSON/CSV/TXT/Markdown/HTML。

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

验证包括 py_compile、focused v1108 tests（`5 passed in 0.35s`）、source hygiene（`2287/2287 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1108/图片/v1108-receipt-index-review.png
```

## 链路角色

v1108 位于 index 之后、receipt recording 之前。它把 v1107 index 从“可查找”推进为“已审阅、可被记录为下一份 lookup-only receipt”，同时继续阻止任何 production promotion 解释。

## 一句话总结

v1108 给 v1107 receipt index 增加了可阻断的审阅层，让下一次 receipt recording 有明确、可复核的准入证据。

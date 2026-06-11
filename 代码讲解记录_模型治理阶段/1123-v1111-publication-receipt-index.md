# v1111 publication receipt index

## 本版目标与边界

v1111 的目标是把 v1109 lookup-only receipt 和 v1110 contract check 合并成一份 receipt index。它为下一步 review 提供统一读取面：receipt 是哪一份、check 是否证明 receipt 可重建、source evidence 是否完整、lookup scope 是否仍然保守。

本版不训练模型，不把 lookup-ready 解释成 production-ready，不打开 promotion。它只把已记录且已 contract-check 的 receipt 包装成可审阅索引。

## 前置路线

本版承接：

```text
v1108 review -> v1109 receipt -> v1110 contract check -> v1111 index
```

v1109 记录了 v1108 review，v1110 证明 v1109 receipt 可以从 v1108 review 重建。v1111 把这两份证据合并成后续 v1112 可审阅的 index。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1111.py
```

核心 index builder，读取 receipt 与 receipt-check report，生成 lookup row、source evidence rows、checks、summary 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1111_artifacts.py
```

artifact writer，输出 JSON/CSV/TXT/Markdown/HTML。JSON 给 v1112 review 消费，HTML/Markdown 给人工审阅。

```text
scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1111.py
```

CLI 入口，显式要求 `--receipt` 和 `--receipt-check`，并支持 `--require-index-ready`、`--require-lookup-ready`。

## 输入与输出

真实输入：

```text
f/1109/解释/receipt-v1109
f/1110/解释/receipt-check-v1110
```

真实输出：

```text
f/1111/解释/receipt-index-v1111
```

输出 report 包含：

```text
status
decision
failed_count
receipt_index
source_receipt
source_receipt_check
check_rows
summary
interpretation
```

`receipt_index` 保存 lookup rows、source evidence、contract check 摘要和 promotion boundary。`summary` 则提供后续 review 的稳定读取面：

```text
index_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
next_step=review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1111
```

## 核心流程

1. CLI 定位 v1109 receipt JSON。
2. CLI 定位 v1110 contract check JSON。
3. builder 读取 receipt summary、check summary 和 check comparison。
4. builder 生成单条 lookup row，保存 receipt id/status、granted use、lookup key 和 source path。
5. builder 生成两条 source evidence，分别绑定 receipt 与 contract check。
6. `_checks` 验证 receipt pass、check pass、lookup-only scope、source evidence 数量、lookup key 数量、contract-check readiness 和 no-promotion。
7. artifact writer 输出 sidecar。
8. Playwright MCP 打开 HTML 并截图，确认人工审阅区块可见。

## 关键检查

- `receipt_passed`：保护 v1109 receipt 是 pass。
- `receipt_check_passed`：保护 v1110 check 是 pass。
- `receipt_check_ready`：保护 check 不是空壳。
- `lookup_scope_matches`：保护用途仍是 `downstream_governance_lookup_only`。
- `lookup_key_count_is_one`：保护查找入口稳定。
- `source_evidence_count_is_two`：保护 receipt 和 check 两类来源都保留。
- `promotion_ready_false`：保护 index 不打开生产 promotion。

## 测试覆盖

focused tests 覆盖合法 index、失败 check、lookup scope 篡改、CLI gating 和 artifact 输出。测试重点是保护 receipt/check 配对关系，以及 lookup-only/no-promotion 边界。

## 运行证据

真实 CLI 输出确认：

```text
status=pass
index_ready=True
lookup_scope=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

验证包括 py_compile、focused v1111 tests（`4 passed in 0.33s`）、source hygiene（`2299/2299 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1111/图片/v1111-receipt-index.png
```

## 链路角色

v1111 位于 contract check 之后、review 之前。它把 v1109 receipt 和 v1110 check 变成统一索引，让 v1112 能审阅一个稳定入口，而不是散落的两个 artifact。

## 一句话总结

v1111 把 v1109 receipt 与 v1110 contract check 合并为可审阅、可查找、仍保持 no-promotion 的治理索引。

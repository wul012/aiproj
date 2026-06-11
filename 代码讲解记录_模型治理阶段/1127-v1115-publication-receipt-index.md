# v1115 publication receipt index

## 本版目标与边界

v1115 的目标是把 v1113 lookup-only receipt 和 v1114 contract check 合并为一份 downstream lookup index。它让后续 review 能从一个统一入口读取 receipt、contract check、source evidence 和 lookup key。

本版不训练模型，不修改 v1113 receipt 或 v1114 check，不把 index 解释成 production approval。index 的 `lookup_scope` 仍然是 `downstream_governance_lookup_only`，`promotion_ready` 仍然是 False。

## 前置路线

v1115 承接：

```text
v1113 receipt -> v1114 contract check -> v1115 index
```

v1113 记录 receipt，v1114 证明 receipt 可从 v1112 review 重建。v1115 则把这两份证据放入同一个 lookup index，供 v1116 审阅。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1115.py
```

核心 index builder。它读取 receipt 和 receipt check，生成 receipt index row、source evidence rows、check rows、summary 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1115_artifacts.py
```

artifact writer，输出 JSON、CSV、TXT、Markdown、HTML。JSON 给 v1116 review 消费，HTML/Markdown 给人工查看索引内容。

```text
scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1115.py
```

CLI 入口。它要求显式传入 `--receipt` 和 `--receipt-check`，并支持 `--require-index-ready`、`--require-lookup-ready`、`--force`。

```text
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1115.py
```

专项测试覆盖合法 index、receipt/check mismatch、source evidence 缺失、CLI gating 和 artifact 输出。

## 输入与输出

真实输入：

```text
f/1113/解释/receipt-v1113
f/1114/解释/receipt-check-v1114
```

真实输出：

```text
f/1115/解释/receipt-index-v1115
```

输出 report 的关键字段包括：

```text
status
decision
receipt_path
receipt_check_path
receipt_index
receipt_index_rows
source_evidence_rows
check_rows
summary
interpretation
```

`receipt_index_rows` 是下游 lookup 的核心表。它绑定：

```text
lookup_key
receipt_index_id
receipt_id
receipt_status
granted_use
source_receipt_path
source_receipt_check_path
source_review_path
source_receipt_index_path
contract_check_ready
promotion_ready
```

`source_evidence_rows` 保存 receipt 和 receipt check 的路径、SHA-256 和 pass 状态，给后续 review 做完整性检查。

## 核心流程

1. CLI 显式接收 v1113 receipt 和 v1114 receipt check。
2. builder 读取 receipt summary、receipt body、contract check summary 和 source evidence。
3. builder 确认 receipt 与 check 指向同一份 receipt，且 check 已通过。
4. builder 生成唯一 lookup key 和一条 receipt index row。
5. `_checks` 验证 lookup scope、granted use、contract-check readiness、source evidence、lookup key 数量和 no-promotion。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML，确认 `Receipt Index Rows`、`Source Evidence`、`Checks` 可见并截图。

## 关键检查

- `receipt_file_exists` 和 `receipt_check_file_exists`：保护两份输入 artifact 存在。
- `receipt_passed`：保护 v1113 receipt 是 pass。
- `receipt_check_passed`：保护 v1114 contract check 是 pass。
- `contract_check_ready`：保护 receipt 已经通过重建式检查。
- `receipt_status_matches_check`：保护 check 对应同一份 receipt。
- `lookup_scope_downstream`：保护 index 只服务 downstream governance lookup。
- `granted_use_lookup_only`：保护用途不扩张。
- `lookup_key_count_is_one`：保护 lookup key 数量稳定。
- `source_evidence_count_is_two`：保护 receipt 和 receipt check 两类证据都保留。
- `promotion_ready_false`：保护 index 不打开 production promotion。

这些检查让 index 成为下游可查的治理入口，而不是松散路径列表。

## 测试覆盖

focused tests 覆盖：

- 合法 v1113 receipt 与 v1114 check 可以生成 ready index。
- receipt/check mismatch 会失败。
- source evidence 缺失会失败。
- CLI `--require-index-ready` 和 `--require-lookup-ready` 能阻断失败结果。
- artifact writer 生成 JSON/CSV/TXT/Markdown/HTML。

测试重点是保护 receipt 和 check 的同源关系，以及 lookup-only 范围。

## 运行证据

真实 CLI 输出：

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

验证包括 py_compile、focused v1115 tests（`4 passed in 0.45s`）、source hygiene（`2315/2315 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1115/图片/v1115-receipt-index.png
```

## 链路角色

v1115 位于 contract check 之后、review 之前。它把 v1113 receipt 与 v1114 check 打包成可查 index，下一步 v1116 会审阅这份 index 是否可以进入下一轮 receipt recording。

## 一句话总结

v1115 把 v1113 receipt 和 v1114 contract check 合并为 lookup-only index，为后续 review 提供单一、可校验入口。

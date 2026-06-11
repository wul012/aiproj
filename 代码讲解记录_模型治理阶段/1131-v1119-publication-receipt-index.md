# v1119 publication receipt index

## 本版目标与边界

v1119 的目标是把 v1117 lookup-only receipt 和 v1118 contract check 合并为一份 downstream lookup index。它让后续 review 能从一个统一入口读取 receipt、contract check、source evidence 和 lookup key。

本版不训练模型，不修改 v1117 receipt 或 v1118 check，不把 index 解释成 production approval。index 的 `lookup_scope` 仍然是 `downstream_governance_lookup_only`，`promotion_ready` 仍然是 False。

## 前置路线

v1119 承接：

```text
v1117 receipt -> v1118 contract check -> v1119 index
```

v1117 记录 receipt，v1118 证明 receipt 可从 v1116 review 重建。v1119 则把这两份证据放入同一个 lookup index，供 v1120 审阅。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1119.py
```

核心 index builder。它读取 receipt 和 receipt check，生成 receipt index row、source evidence rows、check rows、summary 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1119_artifacts.py
```

artifact writer，输出 JSON、CSV、TXT、Markdown、HTML。JSON 给 v1120 review 消费，HTML/Markdown 给人工查看索引内容。

```text
scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1119.py
```

CLI 入口。它要求显式传入 `--receipt` 和 `--receipt-check`，并支持 `--require-index-ready`、`--require-lookup-ready`、`--force`。

## 输入、输出与核心流程

真实输入：

```text
f/1117/解释/receipt-v1117
f/1118/解释/receipt-check-v1118
```

真实输出：

```text
f/1119/解释/receipt-index-v1119
```

核心流程是：读取 receipt 和 receipt check，确认二者同源且 check 已通过，生成唯一 lookup key 和一条 receipt index row，保留 receipt/check 的 SHA-256 source evidence，然后输出 JSON/CSV/TXT/Markdown/HTML。

## 关键检查

- `receipt_file_exists` 和 `receipt_check_file_exists`：保护两份输入 artifact 存在。
- `receipt_passed`：保护 v1117 receipt 是 pass。
- `receipt_check_passed`：保护 v1118 contract check 是 pass。
- `contract_check_ready`：保护 receipt 已经通过重建式检查。
- `receipt_status_matches_check`：保护 check 对应同一份 receipt。
- `lookup_scope_downstream`：保护 index 只服务 downstream governance lookup。
- `granted_use_lookup_only`：保护用途不扩张。
- `lookup_key_count_is_one`：保护 lookup key 数量稳定。
- `source_evidence_count_is_two`：保护 receipt 和 receipt check 两类证据都保留。
- `promotion_ready_false`：保护 index 不打开 production promotion。

## 测试覆盖

focused tests 覆盖合法 index、receipt/check mismatch、source evidence 缺失、CLI gating 和 artifact 输出。测试重点是保护 receipt 和 check 的同源关系，以及 lookup-only 范围。

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

验证包括 py_compile、focused v1119 tests（`4 passed in 0.38s`）、source hygiene（`2331/2331 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1119/图片/v1119-receipt-index.png
```

## 链路角色

v1119 位于 contract check 之后、review 之前。它把 v1117 receipt 与 v1118 check 打包成可查 index，下一步 v1120 会审阅这份 index 是否可以进入下一轮 receipt recording。

## 一句话总结

v1119 把 v1117 receipt 和 v1118 contract check 合并为 lookup-only index，为后续 review 提供单一、可校验入口。

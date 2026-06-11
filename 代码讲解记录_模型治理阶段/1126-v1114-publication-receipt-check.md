# v1114 publication receipt contract check

## 本版目标与边界

v1114 的目标是对 v1113 lookup-only receipt 做重建式 contract check。它读取 v1113 receipt，找到其中记录的 v1112 review，再重新构建一份 receipt，并把原始 receipt 与重建 receipt 的关键字段逐项对比。

本版不训练模型，不修改 v1113 receipt，不把 contract check 解释成 production approval。`contract_check_ready=True` 只表示 receipt 可重建、可复核，并且仍然处在 downstream governance lookup 边界内。

## 前置路线

v1114 承接：

```text
v1112 review -> v1113 receipt -> v1114 contract check
```

v1113 把 v1112 review 固化为 lookup-only receipt。v1114 的职责是证明这份 receipt 没有脱离源 review，也没有在用途、lookup key、source path 或 promotion 字段上发生漂移。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1114.py
```

核心 contract-check builder。它读取 v1113 receipt，解析 source review 路径，重新调用 v1113 receipt builder，并生成对比 summary、check rows 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1114_artifacts.py
```

artifact writer，输出 JSON、CSV、TXT、Markdown、HTML。JSON 给 v1115 index 消费，Markdown/HTML 给人工核对。

```text
scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1114.py
```

CLI 入口。`--require-pass` 会把 contract check 失败转成非零退出码。

```text
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1114.py
```

专项测试覆盖可重建 receipt、granted use 篡改、source review 缺失、source digest 篡改、CLI gating 和 artifact 输出。

## 输入与输出

真实输入：

```text
f/1113/解释/receipt-v1113
```

真实输出：

```text
f/1114/解释/receipt-check-v1114
```

输出 report 的关键字段包括：

```text
status
decision
failed_count
receipt_path
source_receipt_index_review_path
source_receipt_index_review
original_receipt
rebuilt_receipt
comparison
check_rows
summary
interpretation
```

`comparison` 是核心对比面，保存原始和重建 receipt 的 status、granted use、lookup key count、source evidence count、promotion readiness 和 source hash 等字段。

## 核心流程

1. CLI 定位 v1113 receipt JSON。
2. builder 读取 original receipt 和 summary。
3. builder 从 receipt 中读取 `receipt_index_review_path`，加载 v1112 review。
4. builder 调用 v1113 receipt builder，基于同一份 v1112 review 重新生成 rebuilt receipt。
5. `_checks` 对比 original 与 rebuilt 的 receipt id、status、consumer、granted use、lookup keys、source evidence、hash、source paths 和 promotion boundary。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML，确认 `Contract Summary` 和 `Checks` 可见并保存截图。

## 关键检查

- `receipt_file_exists`：保护 v1113 receipt 文件存在。
- `receipt_passed`：保护原始 receipt 本身是 pass。
- `source_review_file_exists`：保护 source v1112 review 仍可追溯。
- `source_review_hash_matches`：保护 receipt 中记录的 source hash 没有漂移。
- `rebuilt_receipt_passed`：保护从 source review 重新构建出来的 receipt 仍能通过。
- `receipt_status_matches`：保护原始与重建 receipt status 一致。
- `consumer_name_matches`：保护消费方没有被替换。
- `granted_use_matches`：保护用途仍是 lookup-only。
- `lookup_keys_match`：保护 lookup key 没有丢失或扩张。
- `source_paths_match`：保护 source receipt、check、review、index 路径一致。
- `promotion_ready_matches_false`：保护原始与重建都没有打开 production promotion。

这些检查让 contract check 成为 receipt 的防篡改入口，而不是普通摘要。

## 测试覆盖

focused tests 覆盖：

- 合法 v1113 receipt 可以从 v1112 review 重建并通过。
- 篡改 granted use 会失败。
- 删除 source review 会失败。
- 篡改 source review hash 会失败。
- CLI `--require-pass` 能阻断失败结果。
- artifact writer 生成 JSON/CSV/TXT/Markdown/HTML。

测试保护的是“receipt 必须能从源 review 推导出来”的契约。

## 运行证据

真实 CLI 输出：

```text
status=pass
contract_check_ready=True
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_lookup_key_count=1
rebuilt_lookup_key_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

验证包括 py_compile、focused v1114 tests（`6 passed in 0.28s`）、source hygiene（`2311/2311 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1114/图片/v1114-receipt-check.png
```

## 链路角色

v1114 位于 receipt 之后、index 之前。它证明 v1113 receipt 能从 v1112 review 重新推导出来，下一步 v1115 可以把 receipt 和 contract check 合并进 lookup-only index。

## 一句话总结

v1114 给 v1113 receipt 增加了可重建、可阻断的 contract check，保证后续 index 消费的是未漂移的 lookup-only receipt。

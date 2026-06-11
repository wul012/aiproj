# v1110 publication receipt contract check

## 本版目标与边界

v1110 的目标是对 v1109 lookup-only receipt 做重建式 contract check。它读取原始 v1109 receipt，再根据 receipt 里保存的 v1108 review 路径重新运行 v1109 receipt builder，确认两份 receipt 在关键字段上一致。

本版不训练模型，不修改 receipt，不改变授权用途。它只验证 v1109 receipt 没有被篡改、路径没有丢失、source review digest 没有漂移，且 production promotion 仍然关闭。

## 前置路线

本版承接：

```text
v1107 index -> v1108 review -> v1109 receipt -> v1110 contract check
```

v1109 已把 v1108 review 记录为 lookup-only receipt。v1110 的任务是回到 v1108 review 再生成一次 receipt，用重建结果校验 v1109。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1110.py
```

核心 contract check 模块，负责定位 receipt、读取 source review、重建 receipt、生成 comparison 和 check rows。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1110_artifacts.py
```

artifact writer，输出 JSON/CSV/TXT/Markdown/HTML。JSON 给 v1111 index 消费，HTML/Markdown 给人工复核。

```text
scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1110.py
```

CLI 入口，支持 receipt 文件或目录输入，`--require-pass` 在 contract check 失败时返回非零。

```text
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1110.py
```

专项测试覆盖合法 receipt、篡改字段、缺失 source review、篡改 source digest、CLI require-pass 和 artifact 输出。

## 输入与输出

真实输入：

```text
f/1109/解释/receipt-v1109
```

真实输出：

```text
f/1110/解释/receipt-check-v1110
```

输出 report 包含：

```text
status
decision
failed_count
issues
source_receipt_path
source_receipt
rebuilt_receipt
comparison
check_rows
summary
interpretation
```

`comparison` 是本版核心证据，保存 original/rebuilt 的 receipt status、granted use、lookup key count、source evidence count、source review hash 和 promotion boundary。

## 核心流程

1. CLI 定位 v1109 receipt JSON。
2. builder 读取原始 receipt report。
3. 根据 `receipt_index_review_path` 定位 v1108 review。
4. 调用 v1109 receipt builder 重建 receipt。
5. `_checks` 对比 status、decision、receipt id/status、consumer、granted use、lookup keys、source evidence、source review hash 和 promotion 字段。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML，确认 `Contract Summary` 和 `Checks` 可见并截图。

## 关键检查

- `source_receipt_file_exists`：保护 v1109 receipt 文件存在。
- `source_review_file_exists`：保护 receipt 引用的 v1108 review 可读取。
- `rebuilt_receipt_passed`：保护重建过程成功。
- `status_matches` 和 `decision_matches`：保护 report 语义一致。
- `receipt_status_matches`：保护 receipt 状态没有漂移。
- `granted_use_matches`：保护用途仍是 lookup-only。
- `lookup_key_count_matches`：保护 lookup key 数量稳定。
- `source_evidence_count_matches`：保护来源证据数量一致。
- `source_review_sha256_matches`：保护 receipt 仍绑定同一份 v1108 review。
- `promotion_ready_matches_false`：保护原始和重建结果都没有打开 promotion。

## 测试覆盖

focused tests 覆盖：

- 合法 v1109 receipt 可以通过 contract check。
- 篡改 granted use 会失败。
- 删除 source review path 会失败。
- 改动 source evidence digest 会失败。
- CLI `--require-pass` 对失败 check 返回非零。
- artifact writer 生成完整 sidecar。

测试保护的是“从 source review 重建 receipt 后必须一致”的核心契约。

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

验证包括 py_compile、focused v1110 tests（`6 passed in 0.33s`）、source hygiene（`2295/2295 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1110/图片/v1110-receipt-check.png
```

## 链路角色

v1110 位于 receipt 之后、下一轮 index 之前。它让 v1109 receipt 从“已记录”推进为“可从上游 review 重建验证”，为 v1111 汇总 receipt/check 成 index 提供输入。

## 一句话总结

v1110 用重建式 contract check 证明 v1109 receipt 与 v1108 review 保持一致，下一步可以进入 lookup-only index。

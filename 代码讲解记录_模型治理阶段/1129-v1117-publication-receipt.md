# v1117 publication receipt

## 本版目标与边界

v1117 的目标是把 v1116 review 记录成下一份 lookup-only downstream receipt。v1116 已经审阅 v1115 index，v1117 负责把这份 review 转成可由下游消费、也可由下一步 contract check 重建验证的 receipt。

本版不训练模型，不修改 v1116 review，不把 receipt 解释成 production approval。receipt 的 `granted_use` 仍然是 `downstream_governance_lookup_only`，`promotion_ready` 仍然是 False。

## 前置路线

v1117 承接：

```text
v1115 index -> v1116 review -> v1117 receipt
```

v1115 建立 lookup index，v1116 审阅该 index，v1117 则把审阅结果以 receipt 形式记录下来，供 v1118 进行重建式 contract check。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1117.py
```

核心 receipt builder，读取 v1116 review，生成 receipt boundary、consumer receipt、checks、summary 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1117_artifacts.py
```

artifact writer，输出 JSON、CSV、TXT、Markdown、HTML。JSON 给 v1118 check 消费，HTML/Markdown 给人工确认边界。

```text
scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1117.py
```

CLI 入口，支持指定 consumer name、requested use、`--require-receipt-ready` 和 `--force`。

```text
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1117.py
```

专项测试覆盖合法 receipt、错误 requested use、source review 路径漂移、source evidence 状态改变、CLI gating 和 artifact 输出。

## 输入与输出

真实输入：

```text
f/1116/解释/receipt-index-review-v1116
```

真实输出：

```text
f/1117/解释/receipt-v1117
```

输出 report 包含 `receipt_index_review_sha256`、`consumer_receipts`、`receipt`、`check_rows`、`summary` 和 `interpretation`。`receipt` 保存 receipt id/status、consumer name、requested/granted use、source review path/hash、lookup keys、source receipt/check/review/index paths 和 no-promotion 字段。

## 核心流程

1. CLI 定位 v1116 review JSON。
2. builder 读取 review summary、review body、source index rows 和 source evidence。
3. builder 检查 requested use 是否仍是 lookup-only。
4. builder 生成 consumer receipt，并绑定 source review 路径与 hash。
5. `_checks` 验证 review ready、lookup scope、receipt row 数量、source evidence 数量、lookup key 数量和 no-promotion。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML，确认 `Receipt Boundary`、`Consumer Receipts`、`Checks` 可见并保存截图。

## 关键检查

- `receipt_index_review_file_exists`：保护 v1116 review JSON 路径没有丢失。
- `receipt_index_review_passed`：保护 v1116 review 本身是 pass。
- `receipt_index_review_decision_ready`：保护 review 决策确实 ready。
- `review_status_allowed`：保护 review 只批准 lookup-only receipt recording。
- `requested_use_allowed`：保护调用者不能把用途改成 production。
- `lookup_only_granted_use`：保护 receipt 输出仍是 lookup-only。
- `source_evidence_count` 和 `source_evidence_digests_present`：保护 source evidence 数量与 digest 完整。
- `promotion_still_false`：保护 receipt 不打开 production promotion。

这些检查让 receipt 成为可阻断的治理记录，而不是普通日志。

## 测试覆盖

focused tests 覆盖：

- 合法 v1116 review 可以生成 ready receipt。
- requested use 被改成非 lookup-only 时失败。
- source review path 漂移时失败。
- source evidence status 被改成 fail 时失败。
- CLI `--require-receipt-ready` 能阻断失败结果。
- artifact writer 生成 JSON/CSV/TXT/Markdown/HTML。

测试重点是保护 receipt boundary 和 requested/granted use 的一致性。

## 运行证据

真实 CLI 输出：

```text
status=pass
receipt_ready=True
granted_use=downstream_governance_lookup_only
receipt_index_row_count=1
source_evidence_count=2
lookup_key_count=1
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

验证包括 py_compile、focused v1117 tests（`6 passed in 0.77s`）、source hygiene（`2323/2323 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1117/图片/v1117-receipt.png
```

## 链路角色

v1117 位于 review 之后、contract check 之前。它把 v1116 review 记录为下游可读 receipt，下一步 v1118 会重新从 v1116 review 构建 receipt，验证 v1117 没有被篡改或误用。

## 一句话总结

v1117 把 v1116 review 转成 lookup-only receipt，为下一轮重建式 contract check 提供可复核输入。

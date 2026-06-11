# v1113 publication receipt

## 本版目标与边界

v1113 的目标是把 v1112 review 记录成下一份 lookup-only downstream receipt。v1112 已经审阅 v1111 index，v1113 负责把这份 review 转成可由下游消费、也可由下一步 contract check 重建验证的 receipt。

本版不训练模型，不修改 v1112 review，不把 receipt 解释成 production approval。receipt 的 `granted_use` 仍然是 `downstream_governance_lookup_only`，`promotion_ready` 仍然是 False。

## 前置路线

v1113 承接：

```text
v1111 index -> v1112 review -> v1113 receipt
```

v1111 建立 lookup index，v1112 审阅该 index，v1113 则把审阅结果以 receipt 形式记录下来，供 v1114 进行重建式 contract check。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1113.py
```

核心 receipt builder，读取 v1112 review，生成 receipt boundary、consumer receipt、checks、summary 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1113_artifacts.py
```

artifact writer，输出 JSON、CSV、TXT、Markdown、HTML。JSON 给 v1114 check 消费，HTML/Markdown 给人工确认边界。

```text
scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1113.py
```

CLI 入口，支持指定 consumer name、requested use、`--require-receipt-ready` 和 `--force`。

```text
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1113.py
```

专项测试覆盖合法 receipt、错误 requested use、source review 路径漂移、source evidence 状态改变、CLI gating 和 artifact 输出。

## 输入与输出

真实输入：

```text
f/1112/解释/receipt-index-review-v1112
```

真实输出：

```text
f/1113/解释/receipt-v1113
```

输出 report 包含：

```text
status
decision
failed_count
receipt_index_review_path
receipt_index_review_sha256
source_receipt_index_review_summary
source_receipt_index_review
receipt_index_rows
source_evidence_rows
consumer_receipts
check_rows
receipt
summary
interpretation
```

`receipt` 是核心对象，保存：

```text
receipt_id
receipt_status
consumer_name
requested_use
granted_use
receipt_index_review_path
receipt_index_review_sha256
lookup_keys
source_receipt_index_path
source_receipt_path
source_receipt_check_path
source_review_path
source_receipt_index_origin_path
promotion_ready
approved_for_promotion
next_step
```

这些字段让后续 v1114 可以从 source review 重新构建 receipt，并比较原始与重建结果。

## 核心流程

1. CLI 定位 v1112 review JSON。
2. builder 读取 review summary、review body、source index rows 和 source evidence。
3. builder 检查 requested use 是否仍是 lookup-only。
4. builder 生成 consumer receipt，并绑定 source review 路径与 hash。
5. `_checks` 验证 review ready、lookup scope、receipt row 数量、source evidence 数量、lookup key 数量和 no-promotion。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML，确认 `Receipt Boundary`、`Consumer Receipts`、`Checks` 可见并保存截图。

## 关键检查

- `receipt_index_review_file_exists`：保护 v1112 review JSON 路径没有丢失。
- `receipt_index_review_passed`：保护 v1112 review 本身是 pass。
- `receipt_index_review_decision_ready`：保护 review 决策确实 ready。
- `receipt_index_review_summary_ready`：保护 summary 和 body 都声明 ready。
- `review_status_allowed`：保护 review 只批准 lookup-only receipt recording。
- `requested_use_allowed`：保护调用者不能把用途改成 production。
- `lookup_only_granted_use`：保护 receipt 输出仍是 lookup-only。
- `receipt_index_lookup_ready`：保护源 index 的 lookup 面可用。
- `contract_check_ready`：保护上游 contract check 被保留。
- `index_rows_present`：保护 receipt 来源只有一条 index row。
- `source_evidence_count` 和 `source_evidence_digests_present`：保护 source evidence 数量与 digest 完整。
- `promotion_still_false`：保护 receipt 不打开 production promotion。

这些检查让 receipt 成为可阻断的治理记录，而不是普通日志。

## 测试覆盖

focused tests 覆盖：

- 合法 v1112 review 可以生成 ready receipt。
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

验证包括 py_compile、focused v1113 tests（`6 passed in 0.56s`）、source hygiene（`2307/2307 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1113/图片/v1113-receipt.png
```

## 链路角色

v1113 位于 review 之后、contract check 之前。它把 v1112 review 记录为下游可读 receipt，下一步 v1114 会重新从 v1112 review 构建 receipt，验证 v1113 没有被篡改或误用。

## 一句话总结

v1113 把 v1112 review 转成 lookup-only receipt，为下一轮重建式 contract check 提供可复核输入。

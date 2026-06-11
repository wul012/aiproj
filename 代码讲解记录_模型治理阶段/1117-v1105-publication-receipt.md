# v1105 publication receipt

本版目标是把 v1104 review 记录成 lookup-only downstream receipt，让后续 contract check 能验证消费来源、用途和 no-promotion 边界。

它不训练模型，不接受 candidate，不改变 v1104 review，不把 lookup receipt 等同于模型质量提升。它只是把已审查的 receipt index review 转成可追踪、可校验、可被下一步检查复核的 receipt artifact。

## 入口

本版入口是 CLI：

```text
scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1105.py
```

核心模块是：

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1105.py
```

CLI 输入 v1104 review 目录或 JSON 文件，输出 JSON/CSV/TXT/Markdown/HTML sidecar。`--require-receipt-ready` 会把 receipt 不可用转成非零退出码；`--require-promotion-ready` 仍会失败，因为本链路不允许 promotion。

## 输出模型

最外层 report 包含：

```text
status
decision
failed_count
issues
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

关键字段是：

```text
receipt_ready=True
granted_use=downstream_governance_lookup_only
promotion_ready=False
approved_for_promotion=False
```

其中 `receipt_index_review_sha256` 是本版证据里的固定锚点，后续 contract check 可以用它确认 receipt 没有脱离源 review。

## 上游证据

本版读取真实上游证据：

```text
f/1104/解释/receipt-index-review-v1104
```

v1104 review 已经审核过 v1103 index，并确认 lookup-only、contract-check-ready 和 no-promotion 边界。v1105 不重算 v1103 index，只消费 v1104 review 的公开结论和源路径。

## 核心流程

1. CLI 定位 v1104 review JSON。
2. builder 读取 review report、summary、review body、receipt index rows 和 source evidence rows。
3. `_checks` 验证 review 通过、ready key、review status、requested use、lookup-only granted use、source rows、source digests、路径存在和 no-promotion boundary。
4. `_receipt` 生成 consumer receipt，并写入 consumer name、requested/granted use、lookup keys、source receipt/index/check paths 和 next step。
5. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
6. Playwright MCP 打开 HTML sidecar 并保存截图到 `f/1105/图片`。

## 关键检查

- `receipt_index_review_file_exists`：保护源 review 文件存在。
- `receipt_index_review_passed` 和 `receipt_index_review_decision_ready`：保护 v1104 review 已经通过。
- `receipt_index_review_summary_ready`：保护 summary 和 review body 同时 ready。
- `requested_use_allowed`：保护调用方只能请求 downstream governance lookup。
- `lookup_only_granted_use`：保护源 review 没有把用途扩大成 promotion。
- `source_evidence_digests_present`：保护两份源证据都带 digest。
- `source_receipt_file_exists`、`source_receipt_check_file_exists`、`source_review_file_exists`：保护证据链路径仍可追踪。
- `promotion_still_false`：保护 receipt recording 不越权打开生产发布。
- `source_next_step_matches`：保护 v1104 review 的 next step 确实指向本类 receipt recording。

## 测试覆盖

专项测试覆盖：

- 合法 v1104 review 可以生成 receipt。
- requested use 被改成 production promotion 时失败。
- source review path 漂移时失败。
- source evidence status 改成 fail 时失败。
- `--require-receipt-ready` 对坏 review 返回非零。
- artifact writer 和 CLI 输出 JSON/CSV/TXT/Markdown/HTML。

这些测试保护的是 receipt 的消费契约，而不是单纯检查文本输出。

## 运行证据

真实命令消费 `f/1104/解释/receipt-index-review-v1104`，输出确认：

- `status=pass`
- `receipt_ready=True`
- `receipt_index_row_count=1`
- `source_evidence_count=2`
- `lookup_key_count=1`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

验证侧跑了 focused v1105 tests（`6 passed in 0.62s`）、py_compile、source hygiene（`2275/2275 clean`）、`git diff --check` 和真实 CLI。Playwright MCP 页面快照确认 HTML 中存在 `Receipt Boundary`、`Consumer Receipts` 和 `Checks`，截图保存为 `f/1105/图片/v1105-receipt.png`。

## 链路角色

v1105 位于这一轮链路的 receipt recording 位置：

```text
v1101 receipt -> v1102 contract check -> v1103 index -> v1104 review -> v1105 receipt
```

下一步是 contract check，不是 promotion。

## 一句话总结

v1105 把 v1104 review 从“已审查”推进为“已被 lookup-only receipt 记录、可由下一步 contract check 复核”的治理证据。

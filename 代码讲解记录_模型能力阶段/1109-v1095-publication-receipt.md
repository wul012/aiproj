# v1095 publication receipt

## 本版目标

v1095 的目标是把 v1094 review 过的 receipt index 记录为 downstream lookup-only receipt。它说明某个下游治理消费者可以读取这份 evidence，但只能用于治理查阅，不能把它解释成 candidate 被接受或模型可生产发布。

本版解决的是 review 结果进入下游前缺少“谁消费、消费什么、允许怎么用”的 receipt 记录问题。

本版不做的事：

- 不训练模型。
- 不接受 candidate。
- 不修改 v1094 review。
- 不放开 production promotion。
- 不把 receipt 当作模型质量提升证据。

## 路线来源

v1091 曾经把 v1090 review 记录成 lookup-only receipt。v1095 复用同一模式，只把源 review 推进到 v1094。这样 v1093-v1095 的链路变成：

```text
v1093 index -> v1094 review -> v1095 receipt
```

下一步自然进入 v1096 contract check，用源 v1094 review 重建 v1095 receipt。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1095.py`
  - v1095 receipt builder。
  - 读取 v1094 review，校验 review ready、lookup-only use、source evidence、source paths、no-promotion 和 next-step routing。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1095_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1095.py`
  - CLI 入口。
  - 输入 v1094 review 目录或 JSON 文件，支持 `--require-receipt-ready`。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1095.py`
  - 覆盖 ready receipt、review 篡改、lookup use 篡改、source path 缺失、promotion 被误打开和 CLI 输出。
- `e/1095/解释/receipt-v1095/`
  - 本版真实运行证据目录。

## 核心数据结构

receipt 输出包含：

- `receipt`
  - 记录 receipt status、consumer name、granted use、source review path、source receipt/index/check 路径、lookup key count 和 promotion boundary。
- `consumer_receipts`
  - 表示下游 lookup reader 获得的只读消费许可。
- `source_review_summary`
  - 保留 v1094 review 的 summary，用来证明 receipt 来源。
- `check_rows`
  - 25 项检查结果，保护 review ready、lookup-only use、source evidence 数量、路径存在、model quality claim bounded、promotion false 和 next-step routing。
- `summary`
  - 汇总 receipt readiness、receipt status、consumer name、granted use、lookup count、promotion boundary 和下一步 contract check。

## 核心流程

1. CLI 定位 v1094 review JSON。
2. builder 读取 review report、review summary、review body、index rows 和 source evidence。
3. `_checks` 验证 v1094 review ready、lookup-ready、contract-check-ready、source paths、lookup-only use 和 no-promotion boundary。
4. `_receipt` 生成 lookup-only receipt body 和 consumer receipts。
5. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
6. Playwright MCP 打开 HTML sidecar 并保存截图。

## 测试覆盖

- 合法 v1094 review 可以生成 receipt。
- 篡改 review decision 会失败，保护源 review 可信。
- 篡改 granted use 会失败，保护只读边界。
- 删除 source path 会失败，保护证据可追溯。
- 打开 promotion 会失败，保护本阶段不越权。
- CLI 能输出 sidecar，并在 require 模式下把失败状态转为退出码。

## 运行证据

真实命令消费 `e/1094/解释/receipt-index-review-v1094`，输出确认：

- `status=pass`
- `receipt_ready=True`
- `granted_use=downstream_governance_lookup_only`
- `receipt_index_row_count=1`
- `source_evidence_count=2`
- `lookup_key_count=1`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP 页面快照确认 HTML 中存在 `Receipt Boundary`、`Consumer Receipts` 和 `Checks`，截图保存为 `e/1095/图片/v1095-receipt.png`。

## 验证

- focused v1095 tests：`6 passed in 0.69s`
- py_compile：新增模块、artifact writer、CLI 和测试均通过
- real CLI evidence：生成 JSON/CSV/TXT/Markdown/HTML sidecar
- Playwright MCP screenshot：`e/1095/图片/v1095-receipt.png`
- full pytest：`2870 passed in 571.77s`
- source hygiene：`2243/2243 clean`
- `git diff --check` 在提交前作为收口验证执行

## 一句话总结

v1095 把 v1094 review 从“通过审查”推进为“已有明确消费者、用途和边界的 lookup-only receipt 证据”。

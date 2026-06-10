# v1071 publication receipt 代码讲解

## 本版目标和边界

v1071 的目标是把 v1070 的 receipt-index review 记录成 downstream lookup receipt。
它不是新治理链，而是继续收口 lookup-only 证据链：v1069 生成 index，v1070 审阅 index，v1071 记录下游 lookup 消费 receipt。
本版不训练模型，不改变 checkpoint，不提升 production promotion，只证明“这个 review 可以被下游以 lookup-only 方式消费”。

## 前置链路

1. v1069：把 v1067 receipt 和 v1068 contract check 编成 receipt index。
2. v1070：对 v1069 index 做只读 review，确认 lookup scope、source evidence、next step 和 no-promotion 边界。
3. v1071：把 v1070 review 写成 receipt，作为下一步 contract check 的输入。

这条链路的价值是把“可读审阅结果”转换成“可复核消费凭证”。

## 关键新增文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1071.py`
  - 核心 receipt builder。
  - 读取 v1070 review，校验 review ready、lookup-only use、source evidence、source paths、source next step 和 promotion 边界。
  - 输出 `receipt`、`consumer_receipts`、`summary`、`check_rows` 和 `interpretation`。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1071_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
  - CSV 面向后续索引或人工比对，HTML 面向截图和审阅。
- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1071.py`
  - CLI 入口。
  - 接收 v1070 review JSON 或输出目录。
  - `--require-receipt-ready` 可作为自动化 gate。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1071.py`
  - 覆盖 ready path、用途篡改、source path 漂移、source evidence 状态漂移、CLI gate 和 artifact wiring。
- `e/1071/解释/receipt-v1071/`
  - 真实 CLI 输出，是本版最终证据。
- `e/1071/图片/v1071-receipt.png`
  - Playwright MCP 截图证据。

## 核心数据结构

### `receipt`

`receipt` 是本版最重要的交接对象，包含：

- `receipt_id`
- `consumer_name`
- `granted_use`
- `receipt_index_review_path`
- `source_receipt_index_path`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_origin_path`
- `next_step`

它明确说明 v1071 消费的是 v1070 review，而不是直接绕过 review 去消费更早的 index。

### `consumer_receipts`

`consumer_receipts` 是可索引的下游消费记录。每一行保留：

- consumer name
- lookup key
- receipt index id
- source receipt id
- generated receipt id
- granted use
- promotion readiness
- receipt status

这里的 `granted_use` 固定为 `downstream_governance_lookup_only`，`promotion_ready` 固定保持 `False`。

### `check_rows`

`check_rows` 覆盖 25 项检查，核心包括：

- v1070 review 文件存在。
- review summary 与 body 都 ready。
- lookup scope、consumer boundary、model quality claim 没有漂移。
- source receipt index、source receipt、source check、source review、origin index 路径仍然存在。
- source evidence 行数为 2 且状态为 pass。
- source next step 指向 receipt 记录。
- requested use 仍然是 lookup-only。

这些检查保护的不是模型输出质量，而是证据交接边界。

## 运行流程

1. CLI 接收 `e/1070/解释/receipt-index-review-v1070`。
2. `locate_receipt_index_review_v1071()` 定位 v1070 review JSON。
3. `build_..._receipt_v1071()` 构造 receipt、consumer rows、summary 和 check rows。
4. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
5. `resolve_exit_code()` 根据 `--require-receipt-ready` 和 `--require-promotion-ready` 返回自动化退出码。

## 测试覆盖

focused 测试结果：
```text
6 passed in 0.87s
```

测试保护点：

- ready review 能生成 ready receipt。
- requested use 改成 production promotion 会失败。
- source review path 漂移会失败。
- source evidence 状态改成 fail 会失败。
- CLI 在 `--require-receipt-ready` 下会对坏 review 返回 `1`。
- artifact writer 和 CLI 输出文件命名一致。

全量验证待回填：

- full pytest: `2744 passed in 667.19s`
- source hygiene: `status=pass`, `source_count=2146`, `clean_count=2146`, `bom_count=0`, `syntax_error_count=0`, `compatibility_error_count=0`

## 运行证据

真实 CLI 输出确认：

- `status=pass`
- `receipt_ready=True`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP 截图：

- `e/1071/图片/v1071-receipt.png`

## 一句话总结

v1071 把 v1070 的只读 review 转成可消费 receipt，让下一步 contract check 拿到稳定、可追溯、仍然保持 lookup-only 边界的输入。

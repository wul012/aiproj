# v1086 publication receipt index review

## 本版目标

v1086 的目标是审阅 v1085 receipt index，确认它可以进入下一步 lookup-only receipt recording。它不是新的模型能力，不是训练结果，也不是 promotion gate，而是 receipt index 到 receipt recording 之间的只读审阅层。

本版不做的事：

- 不训练模型
- 不接受 candidate
- 不打开 production promotion
- 不修改 v1085 index，只读消费它

## 路线来源

v1085 已经把 v1083 receipt 和 v1084 contract check 收束成一份 digest-backed index。v1086 检查这份 index 的 source evidence、lookup key、contract check ready 状态和 no-promotion 边界，确认它能作为下一版 receipt 的输入。

这条路线仍然是证据链治理。它增强的是可复核性，不是模型本身生成能力。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1086.py`
  - 核心 review builder。
  - 读取 v1085 index，验证 lookup-only scope、index row、source evidence、contract check ready 和 next-step 边界。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1086_artifacts.py`
  - 输出 JSON/CSV/TXT/MD/HTML。
  - 这些是审阅证据视图，不是训练产物。

- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1086.py`
  - CLI 入口。
  - 接收 receipt index 目录或 JSON 文件，并写出 review sidecar。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1086.py`
  - 覆盖正常通过、篡改 ready key、source evidence 缺失、lookup key 漂移和 CLI 输出。

- `e/1086/解释/receipt-index-review-v1086/`
  - 真实运行输出目录。
  - 后续 v1087 receipt 会消费这里的 review。

## 核心数据结构

review 结果包含：

- `summary`
  - 保存 `review_status`、`receipt_index_row_count`、`lookup_key_count`、`source_evidence_count`、`lookup_ready`、`contract_check_ready`、`promotion_ready` 和 `next_step`。

- `review`
  - 保存本次审阅对 index 的批准边界。
  - `review_status` 明确是 lookup-only，而不是 promotion approval。

- `checks`
  - 每个检查项都能定位一个 contract 断言。
  - 例如 index ready、lookup key namespace、source evidence count、contract check ready、model quality claim 仍为 educational。

## 核心流程

1. CLI 定位 v1085 index JSON。
2. builder 读取 index summary、receipt index rows 和 source evidence rows。
3. `_checks` 判断 index 是否 ready、lookup key 是否只有一个、source evidence 是否为 2、contract check 是否 ready。
4. 如果没有失败项，输出 `review_ready=True`。
5. artifact writer 生成多格式 sidecar。

## 测试覆盖

- 合法 v1085 index 可以通过，保护正常 handoff。
- 篡改 ready key 会失败，保护 index readiness。
- 删除 source evidence 会失败，保护证据链完整性。
- lookup key 漂移会失败，保护命名空间稳定。
- CLI sidecar 写出，保护真实归档流程。

## 运行证据

真实命令输出确认：

- `status=pass`
- `review_ready=True`
- `receipt_index_row_count=1`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=22`
- `failed_check_count=0`

Playwright MCP snapshot 确认页面显示 `Status pass`、`Review ready True`、`Rows 1`、`Lookup keys 1`、`Evidence 2`、`Failed 0`，并能看到 v1085 index、v1083 receipt、v1084 check 和 next-step 路由。

## 验证

- focused v1086 tests：`5 passed in 0.48s`
- full pytest：`2822 passed in 593.23s`
- source hygiene：`2207/2207 clean`
- py_compile：新增模块、artifact writer、CLI、测试均通过。
- `git diff --check` 会在提交前执行。

## 一句话总结

v1086 把 v1085 digest-backed index 审阅为可记录 receipt 的 lookup-only 输入，让下一步 receipt recording 有明确的只读批准证据。

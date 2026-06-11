# v1091 publication receipt

## 本版目标

v1091 的目标是把 v1090 review 记录成一份 downstream lookup-only receipt。它承接 v1090 的复核结论，把“index 已复核”转化为“receipt 已记录”，为下一版 contract check 提供可重建、可比对的输入。

它解决的问题是：review 产物虽然能说明 v1089 index 合格，但下游消费链路需要一份 receipt 来表达“谁消费了这份 review、被授予什么使用范围、它的上游路径和 source evidence 是否还在”。v1091 正是这层记录。

本版不做的事：

- 不训练模型。
- 不修改 v1090 review。
- 不接受 candidate。
- 不放开 production promotion。
- 不把 receipt 解释成模型质量提升。

## 路线来源

v1089 生成 digest-backed receipt index，v1090 对它做 review。v1091 接在 v1090 后面，复用 v1087 的 receipt recording 模式，把 source review 从 v1086 升级为 v1090。

这条链路的下一步是 v1092 contract check：它应该从 v1090 review 重新构建 v1091 receipt，并与原始 receipt 比对，防止 receipt 被篡改或路径丢失。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1091.py`
  - 核心 receipt builder。
  - 读取 v1090 review，执行 25 项 check，生成 `receipt`、`consumer_receipts`、`summary` 和 `interpretation`。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1091_artifacts.py`
  - 负责 JSON/CSV/TXT/Markdown/HTML 输出。
- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1091.py`
  - CLI 入口。
  - `receipt_index_review` 是位置参数，支持目录或 JSON 文件。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1091.py`
  - 覆盖正常 receipt、requested use 篡改、source evidence 异常、promotion ready 异常、CLI 失败退出和 sidecar 输出。
- `e/1091/解释/receipt-v1091/`
  - 本版真实运行证据目录。

## 核心数据结构

`receipt` 是本版的核心结构，关键字段包括：

- `receipt_ready`
  - 所有 check 通过时为 `True`。
- `receipt_status`
  - 标识这是一份 lookup-only receipt。
- `consumer_name`
  - 默认消费者是 v1091 lookup reader，说明这是治理消费记录，不是模型推理服务。
- `granted_use`
  - 固定为 `downstream_governance_lookup_only`。
- `receipt_index_review_path`
  - 指向 v1090 review JSON。
- `source_receipt_index_path`
  - 指向被 v1090 review 复核的 v1089 index。
- `source_receipt_path` 和 `source_receipt_check_path`
  - 保留 v1087 receipt 与 v1088 contract check 的追踪路径。
- `promotion_ready`
  - 固定为 `False`。

`consumer_receipts` 是面向下游的展开行，包含 consumer、lookup key、receipt index id、source receipt id、receipt id、granted use、promotion_ready 和 receipt_status。

## 核心流程

1. CLI 接收 v1090 review 目录或 JSON 文件。
2. `locate_receipt_index_review_v1090` 定位 v1090 review JSON。
3. builder 读取 review summary、review body、receipt index rows 和 source evidence rows。
4. `_checks` 执行 25 项断言，确认 review ready、lookup-only use、source evidence、source path、next step 和 promotion boundary。
5. `_receipt` 生成 receipt body 和 consumer receipts。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML 并截图。

## 测试覆盖

- 合法 v1090 review 可以生成 ready receipt。
- requested use 不是 lookup-only 会失败，防止越权使用。
- source evidence 不是 pass 会失败，保护上游证据链。
- promotion ready 被改成 true 会失败，保护 no-promotion 边界。
- CLI 在坏 review 且 `--require-receipt-ready` 下返回 `1`。
- sidecar 输出覆盖 JSON/CSV/TXT/Markdown/HTML。

这些测试把 v1091 定位为“记录型契约模块”，而不是单纯生成文档。

## 运行证据

真实命令消费了 `e/1090/解释/receipt-index-review-v1090`，输出确认：

- `status=pass`
- `receipt_ready=True`
- `receipt_index_row_count=1`
- `source_evidence_count=2`
- `lookup_key_count=1`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP 页面快照确认 HTML 中存在 `Receipt Boundary`、`Consumer Receipts` 和 `Checks`，截图保存为 `e/1091/图片/v1091-receipt.png`。

## 验证

- focused v1091 tests：`6 passed in 0.60s`
- full pytest：`2849 passed in 493.04s`
- source hygiene：`2227/2227 clean`
- py_compile：新增模块、artifact writer、CLI 和测试均通过
- real CLI evidence：生成 JSON/CSV/TXT/Markdown/HTML sidecar
- Playwright MCP screenshot：`e/1091/图片/v1091-receipt.png`
- `git diff --check` 在提交前作为收口验证执行

## 一句话总结

v1091 把 v1090 review 转化为 downstream lookup-only receipt，让下一版可以通过 contract check 验证这份 receipt 是否仍能从源 review 重建出来。

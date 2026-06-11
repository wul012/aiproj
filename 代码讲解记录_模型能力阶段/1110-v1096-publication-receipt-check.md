# v1096 publication receipt contract check

## 本版目标

v1096 的目标是验证 v1095 receipt 是否能从它声明的 v1094 source review 重新推导出来。v1095 已经记录了 downstream lookup-only receipt，但记录本身还需要防篡改：如果 receipt JSON 被改、source review 路径丢失、granted use 被放宽，v1096 应该失败。

本版不做的事：

- 不训练模型。
- 不修改 v1095 receipt。
- 不接受 candidate。
- 不放开 production promotion。
- 不把 contract check 当作模型能力提升。

## 路线来源

v1092 曾经对 v1091 receipt 做过 contract check。v1096 复用同一模式，只把源头升级为：

- 原始 receipt：v1095
- source review：v1094
- rebuilt receipt builder：v1095 builder

这样 v1093-v1096 形成一轮完整证据链：index -> review -> receipt -> contract check。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1096.py`
  - 核心 contract-check builder。
  - 读取 v1095 receipt，解析 source review 路径，重建 receipt，并执行 46 项字段比对。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1096_artifacts.py`
  - 负责 JSON/CSV/TXT/Markdown/HTML 输出。
- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1096.py`
  - CLI 入口。
  - 支持目录或 JSON 文件输入，并提供 `--require-pass` 自动化 gate。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1096.py`
  - 覆盖正常重建、granted use 篡改、source review 缺失、source digest 篡改和 CLI 输出。
- `e/1096/解释/receipt-check-v1096/`
  - 本版真实运行证据目录。

## 核心数据结构

contract check 输出包含：

- `original_summary` 和 `rebuilt_summary`
  - 比对 receipt status、consumer name、granted use、lookup key count、promotion boundary 和 next step。
- `original_receipt` 和 `rebuilt_receipt`
  - 比对 receipt body 中的 source review path、source review digest、source receipt/index/check 路径、review status 和 model quality claim。
- `check_rows`
  - 46 项检查结果。
  - 前置检查保护 source review 是否存在、status/decision/failed_count 是否一致。
  - 字段检查保护 summary、receipt、consumer receipts、lookup-only use、no-promotion 和 next-step 路由。
- `summary`
  - 汇总 original/rebuilt status、use、lookup count、promotion boundary 与下一步 index 路由。

## 核心流程

1. CLI 定位 v1095 receipt JSON。
2. builder 读取原始 receipt report。
3. `_resolve_source_review_path` 从 receipt body 或相对路径定位 v1094 review。
4. `_rebuild_receipt` 调用 v1095 builder，从 v1094 review 重建 receipt。
5. `_checks` 比对原始 receipt 和 rebuilt receipt 的 46 项关键字段。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML 并截图。

## 测试覆盖

- 合法 v1095 receipt 可以通过 contract check。
- 篡改 `granted_use` 会失败，保护 lookup-only 使用边界。
- 删除 source review 会失败，保护上游路径可追踪。
- 篡改 source review digest 会失败，保护内容一致性。
- CLI 能输出 sidecar，并且 `--require-pass` 对失败结果返回 `1`。

这些测试让 v1096 成为防篡改层，而不是简单的报告生成层。

## 运行证据

真实命令消费了 `e/1095/解释/receipt-v1095`，输出确认：

- `status=pass`
- `contract_check_ready=True`
- `original_receipt_status` 与 `rebuilt_receipt_status` 一致。
- `original_granted_use` 与 `rebuilt_granted_use` 均为 `downstream_governance_lookup_only`。
- `original_lookup_key_count=1`
- `rebuilt_lookup_key_count=1`
- `original_promotion_ready=False`
- `rebuilt_promotion_ready=False`
- `passed_check_count=46`
- `failed_check_count=0`

Playwright MCP 页面快照确认 HTML 中存在 `Contract Summary` 和 `Checks`，截图保存为 `e/1096/图片/v1096-receipt-check.png`。

## 验证

- focused v1096 tests：`6 passed in 0.33s`
- py_compile：新增模块、artifact writer、CLI 和测试均通过
- real CLI evidence：生成 JSON/CSV/TXT/Markdown/HTML sidecar
- Playwright MCP screenshot：`e/1096/图片/v1096-receipt-check.png`
- full pytest：`2876 passed in 558.66s`
- source hygiene：`2247/2247 clean`
- `git diff --check` 在提交前作为收口验证执行

## 一句话总结

v1096 把 v1095 receipt 从“已记录”推进为“可重建、可比对、可作为下一步 index 输入”的 contract-checked lookup-only 证据。

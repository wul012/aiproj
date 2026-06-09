# v1044 publication receipt contract check 代码讲解

## 本版目标和边界

v1044 的目标是对 v1043 downstream lookup-only receipt 做一层 contract check。

它解决的问题是：v1043 已经把 v1042-reviewed receipt index 记录成 consumer receipt，但后续模块仍需要确认这个 receipt 可以从源 v1042 review 重新推导出来。否则 receipt JSON 可能出现被手动篡改、source review 路径丢失、digest 漂移、granted use 被改写，或者 next-step 路由与真实源链路不一致的问题。

本版不做：

- 不训练模型。
- 不新增 benchmark、replay 或推理能力。
- 不把 receipt check 解释成模型能力提升。
- 不开启 production promotion。

## 前置链路

v1044 承接 v1041-v1043：

- v1041 把 v1039 receipt 和 v1040 receipt contract check 写成 digest-backed receipt index。
- v1042 review 该 receipt index，确认 lookup-only、source evidence、contract check 和 no-promotion 字段都稳定。
- v1043 记录 downstream lookup-only consumer receipt。
- v1044 读取 v1043 receipt，使用 receipt 内的 v1042 source review 重新生成 receipt，并比较原始和重建结果。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1044.py`
  - v1044 contract check builder。
  - 负责定位 receipt JSON、读取 source review、调用 v1043 receipt builder 重建 receipt，并比较关键字段。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1044_artifacts.py`
  - 负责输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 用于 Playwright MCP 截图，CSV 记录逐项 check row。

- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1044.py`
  - CLI 入口。
  - 支持传入 receipt JSON 或 receipt 输出目录。
  - 支持 `--require-pass`，contract check 失败时返回非 0。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1044.py`
  - 覆盖 ready path、granted use 篡改、source review 缺失、source digest 篡改、CLI 失败退出和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1044 next-step 常量，统一路由到下一步 receipt index。

## 维护性调整

v1044 特意避免从 v1042 review 模块导入 `read_json_report`，而是在本模块内使用轻量 JSON reader。

原因是 v1042 以前的 governance 模块存在很长的历史导入链，在 Windows + pytest assertion rewrite 环境下可能触发递归过深。v1044 只需要读取 JSON，不需要加载历史 builder，所以本地读取更稳、更小、更符合 contract check 的职责。

测试侧也做了同样处理：v1044 测试不再导入 v1043 测试 helper，而是自己构造最小合法 v1042 review fixture。这个 fixture 会创建必要 source 文件、两条 source evidence、一条 lookup row，再交给真实 v1043 builder 生成 receipt。这样测试仍覆盖真实 builder，但不依赖旧测试模块链。

## 核心数据结构

v1044 report 顶层字段包括：

- `status`：contract check 是否通过。
- `decision`：通过时为 v1044 passed decision，失败时指向修复动作。
- `failed_count`：失败 check 数量。
- `issues`：失败 check 的行式列表。
- `receipt_path`：被检查的 v1043 receipt 路径。
- `source_receipt_index_review`：从 receipt 中解析出的 v1042 source review 路径。
- `original_summary` / `rebuilt_summary`：原始 receipt 和重建 receipt 的 summary。
- `original_receipt` / `rebuilt_receipt`：原始 receipt body 和重建 receipt body。
- `check_rows`：逐项比较结果。
- `summary`：给 CLI、TXT、HTML 快速展示的摘要。

## 检查项说明

`_checks` 先比较顶层字段：

- source review 文件是否存在。
- `status` 是否一致。
- `decision` 是否一致。
- `failed_count` 是否一致。
- `receipt_index_review_sha256` 是否一致。
- `consumer_receipts` 是否一致。

然后分别比较 summary 和 receipt body 的固定字段。

summary 重点保护：

- v1043 ready key。
- receipt id/type/status。
- consumer name。
- granted use。
- row count、source evidence count、lookup key count。
- promotion/approved 字段必须仍为 false。
- consumer boundary 和 model quality claim。
- next step。
- passed/failed check count。

receipt body 重点保护：

- receipt ready/id/type/status。
- requested use 和 granted use。
- source review path 与 sha256。
- lookup keys。
- review status。
- source receipt index、source receipt、source receipt check、source review、origin index path。
- no-promotion 字段和 bounded model quality claim。

## 输入输出流程

CLI 流程：

1. `locate_receipt_v1044` 接收 JSON 文件或目录。
2. `read_json_report` 读取 v1043 receipt。
3. `build_randomized_holdout_..._receipt_check_v1044` 解析 source review path。
4. `_rebuild_receipt` 读取 v1042 review，并调用 v1043 builder 重建 receipt。
5. `_checks` 逐项比较 original/rebuilt。
6. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。
7. `--require-pass` 下，如果 `status != pass`，CLI 返回非 0。

## 测试覆盖

聚焦测试验证：

- 合法 receipt 可以重建并通过 contract check。
- 修改 `granted_use` 会让 summary 和 receipt body 两处检查失败。
- source review 路径丢失会失败。
- source review digest 被篡改会失败。
- CLI 在 `--require-pass` 下遇到失败 report 会返回 `SystemExit(1)`。
- writer 真实输出五类 artifact，文本、Markdown、HTML 都包含关键内容。

这些断言保护的是“receipt 与 source review 可复核一致”，不是模型能力本身。

## 运行证据

运行证据归档在：

- `e/1044/解释/receipt-check-v1044`
- `e/1044/图片/v1044-receipt-check.png`

真实 CLI 输出显示：

```text
status=pass
contract_check_ready=True
failed_count=0
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_lookup_key_count=1
rebuilt_lookup_key_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

Playwright MCP 截图确认 HTML 页面可读，页面上能看到 `Status=pass`、`Contract=True`、`Failed=0`、source review、original/rebuilt status 和 checks 表格。

## 一句话总结

v1044 把 v1043 downstream lookup-only receipt 从“已经记录”推进到“可由源 review 重建并逐项复核一致”，同时继续守住不训练、不推广、不扩大模型质量声明的边界。

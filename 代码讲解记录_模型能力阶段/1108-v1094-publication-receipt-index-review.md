# v1094 publication receipt index review

## 本版目标

v1094 的目标是在 v1093 生成 digest-backed receipt index 之后，补一层 review。它确认 v1093 index 真的满足 lookup-only receipt recording 的条件：源 receipt 存在、contract check 已通过、lookup key 唯一、source evidence 有摘要、promotion 仍然关闭。

本版解决的是 index 生成后直接被下游消费的风险。review 层把“可生成”变成“可被下一步 receipt 记录消费”，但它仍然只是治理证据，不代表模型能力提升。

本版不做的事：

- 不训练模型。
- 不接受 candidate。
- 不修改 v1093 index。
- 不生成新的 receipt。
- 不放开 production promotion。

## 路线来源

v1090 曾经 review v1089 index，然后交给 v1091 receipt 记录。v1094 复用同一模式，只把输入更新为 v1093 index，并把下一步路由到 v1095 之前的 v1094 receipt recording。

这让 v1091-v1094 形成第二轮闭环：receipt -> contract check -> index -> review。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1094.py`
  - v1094 review builder。
  - 读取 v1093 index，校验 summary、index body、rows、source evidence 和 next-step 路由。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1094_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1094.py`
  - CLI 入口。
  - 输入为 v1093 index 目录或 JSON 文件，支持 `--require-review-ready` 和 `--require-lookup-ready`。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1094.py`
  - 覆盖 ready review、lookup scope 篡改、source path 缺失、promotion 被误打开和 CLI 输出。
- `e/1094/解释/receipt-index-review-v1094/`
  - 本版真实运行证据目录。

## 核心数据结构

review 输出包含：

- `review`
  - 记录 `review_ready`、`review_status`、receipt index row count、lookup key count、source evidence count、promotion boundary 和下一步。
- `source_receipt_index_summary`
  - 保留 v1093 index 的 summary，供下游确认 index 自身状态。
- `source_receipt_index`
  - 保留 v1093 index body，包含 receipt/check/source evidence 路径。
- `receipt_index_rows`
  - 通过 review 后保留可消费的 lookup row。
- `source_evidence_rows`
  - 保留 receipt 和 contract check 两份源证据的 digest-backed rows。
- `check_rows`
  - 22 项 review 检查，保护 source 文件存在、lookup-only use、contract check ready、promotion false 和 next-step routing。

## 核心流程

1. CLI 定位 v1093 index JSON。
2. builder 读取 index report、summary、index body、rows 和 source evidence。
3. `_checks` 校验 v1093 `decision`、ready key、lookup scope、granted use、source evidence 数量、source 文件存在、contract check ready 和 no-promotion boundary。
4. `_review` 在全部检查通过后生成 review summary，并把下一步指向 v1094 receipt recording。
5. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
6. Playwright MCP 打开 HTML sidecar 并保存截图。

## 测试覆盖

- 合法 v1093 index 可以通过 review。
- 篡改 lookup scope 会失败，保护下游只读边界。
- 删除 source path 会失败，保护证据可追溯。
- 把 promotion 打开会失败，保护本阶段不越权。
- CLI 能输出 sidecar，并把 require gate 接到退出码。

这些测试让 v1094 成为 receipt recording 前的审查层，而不是简单展示层。

## 运行证据

真实命令消费 `e/1093/解释/receipt-index-v1093`，输出确认：

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

Playwright MCP 页面快照确认 HTML 中存在 `Review Summary`、`Receipt Index Rows`、`Source Evidence` 和 `Checks`，截图保存为 `e/1094/图片/v1094-receipt-index-review.png`。

## 验证

- focused v1094 tests：`5 passed in 0.51s`
- py_compile：新增模块、artifact writer、CLI 和测试均通过
- real CLI evidence：生成 JSON/CSV/TXT/Markdown/HTML sidecar
- Playwright MCP screenshot：`e/1094/图片/v1094-receipt-index-review.png`
- full pytest：`2864 passed in 593.43s`
- source hygiene：`2239/2239 clean`
- `git diff --check` 在提交前作为收口验证执行

## 一句话总结

v1094 把 v1093 digest-backed index 从“可查”推进为“经过 review、可进入下一步 lookup-only receipt recording”的治理证据。

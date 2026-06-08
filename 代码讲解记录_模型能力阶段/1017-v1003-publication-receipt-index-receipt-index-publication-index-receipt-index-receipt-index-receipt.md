# v1003 publication receipt index receipt index publication index receipt index receipt index receipt

本版目标是把 v1002 已经 review 通过的 receipt-index-receipt index 记录成一条 lookup-only downstream receipt。它解决的问题是：v1002 证明 v1001 索引可以被下一步消费，但还没有形成“某个治理读者已经接收这份索引”的 receipt 证据。

本版不训练模型，不生成 checkpoint，不扩大模型质量声明，不允许 production promotion。它只记录 lookup-only receipt，并把下一步路由到 v1003 contract check。

## 前置路线

v999 记录 publication index receipt index receipt。v1000 从 v998 review 重新推导 v999 receipt，验证 contract。v1001 把 v999 receipt 与 v1000 check 编入 receipt-index-receipt index。v1002 review v1001 index，确认 lookup scope、source evidence、digest、路径和 no-promotion 边界可被下游 receipt 消费。

v1003 接在 v1002 后面，做的是“正式 receipt 记录”：读取 v1002 review，生成一个 consumer receipt，说明 `publication_index_receipt_index_receipt_index_governance_lookup_reader` 可以以 `downstream_governance_lookup_only` 的权限消费这份索引。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.py`
  - v1003 核心 builder。它读取 v1002 review report，执行 21 项检查，生成 `receipt`、`consumer_receipts`、`summary`、`check_rows` 和 `interpretation`。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003_artifacts.py`
  - v1003 输出层。负责把 report 渲染成 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.py`
  - CLI 入口。支持输入 v1002 JSON 或输出目录，支持 `--require-receipt-ready`、`--require-promotion-ready`、`--consumer-name`、`--requested-use` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.py`
  - v1003 单测。覆盖正常 receipt、requested use 越权、source receipt index 缺失、CLI 失败退出和输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v1003 下一步常量：`check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003`。
- `src/minigpt/__init__.py`
  - 暴露 v1003 build/write 的包级懒加载入口。
- `e/1003/解释/receipt-v1003/*`
  - v1003 真实运行产物。JSON 是后续 contract check 的主要输入，HTML 是人工复核页面。
- `e/1003/图片/v1003-receipt.png`
  - Playwright MCP 运行截图，证明 HTML 可打开且展示 pass、receipt ready、consumer 和 lookup-only use。

## 输入输出

v1003 输入是 v1002 review report。CLI 可以接收：

- `e/1002/解释/review-v1002`
- 或其中的 v1002 JSON 文件

`locate_receipt_index_review_v1003()` 负责把目录解析为 v1002 JSON 文件名。`read_json_report()` 用 `utf-8-sig` 读取，避免历史 BOM 文件导致解析失败。

v1003 输出的核心结构包括：

- `receipt`
  - 本版正式记录的 receipt body。
- `consumer_receipts`
  - 面向下游 reader 的一行 receipt 表，包含 consumer、lookup key、receipt index id、source receipt id、receipt id、granted use、blocked uses、promotion flag 和 receipt status。
- `check_rows`
  - 21 项检查的逐项结果。
- `summary`
  - 面向 README、CLI 文本和后续 check 的稳定摘要。
- `interpretation`
  - 用自然语言说明本版只允许 downstream lookup，不代表模型可生产推广。

## 核心字段语义

`receipt_status` 为：

```text
publication_index_receipt_index_receipt_index_lookup_receipted
```

这说明 v1003 记录的是 receipt-index-receipt 这一层索引的 receipt，而不是旧的 publication index receipt。

`consumer_name` 为：

```text
publication_index_receipt_index_receipt_index_governance_lookup_reader
```

本版特别修正了 CLI 默认值，让 CLI 运行证据与核心 builder 默认值一致。测试也新增了断言，保证以后不会出现 builder 默认正确、CLI 产物仍写旧 consumer 的漂移。

`granted_use` 固定为：

```text
downstream_governance_lookup_only
```

这代表允许后续治理工具读取索引，不允许用于 production promotion、模型质量扩展声明或训练数据声明扩展。

`promotion_ready` 和 `approved_for_promotion` 都固定为 `False`。这两个字段是本版边界的关键：即使 receipt 通过，也不能把它解释成模型能力提升或可上线。

## 检查逻辑

`_checks()` 保护以下内容：

- v1002 review 文件存在。
- v1002 report 本身 `status=pass`。
- v1002 decision 是 ready。
- summary 和 review body 都标记 ready。
- review status 只能是 `approved_for_publication_index_receipt_index_receipt_index_receipt_lookup_only`。
- requested use 必须是 downstream governance lookup only。
- blocked uses 必须完整保留。
- receipt index 和 lookup 都必须 ready。
- source contract check 必须 ready。
- index row 数量必须和 summary 一致，且等于 1。
- source evidence 数量必须和 summary 一致，且等于 2。
- lookup key 必须使用 `publication-index-receipt-index-receipt:` 命名空间。
- index row 不允许 promotion。
- review summary、review body 和 approved flag 都不能打开 promotion。
- consumer boundary 必须保持 `governance_lookup_only`。
- model quality claim 必须保持 `bounded_randomized_target_hidden_holdout_claim_only`。
- source receipt index、source receipt、source receipt check 文件必须仍存在。
- source review failed check count 必须为 0。
- v1002 next step 必须路由到 v1003 receipt。

这些检查的作用是让 receipt 记录只依赖已 review 的稳定字段，同时不重新扩大模型能力解释。

## Artifact 输出

`write_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003_outputs()` 生成五类文件：

- JSON：后续 contract check 的机器输入。
- CSV：一行 consumer receipt，便于快速表格检索。
- TXT：CLI 摘要，便于终端和 CI 日志阅读。
- Markdown：归档说明和人工审阅。
- HTML：Playwright MCP 截图的可视化页面。

HTML 页面分为三个主要区域：

- summary cards：显示 pass、receipt ready、lookup keys、evidence、use 和 failed count。
- Receipt Boundary：显示 receipt status、consumer、source review、source receipt index、source receipt、source check 和 next step。
- Consumer Receipts / Checks：显示下游 receipt 行与 21 项检查。

这些产物是最终证据，不是临时文件。后续版本可以消费 JSON，也可以用 HTML 截图证明人工可审阅性。

## CLI 行为

CLI 命令：

```powershell
python scripts\record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1003.py e\1002\解释\review-v1002 --out-dir e\1003\解释\receipt-v1003 --require-receipt-ready --force
```

`--require-receipt-ready` 会在 receipt 未通过时返回 1。`--require-promotion-ready` 仍会返回 1，因为本版明确不允许 promotion。`--force` 只用于替换同一输出目录，避免旧证据残留。

本版还修正了 CLI 默认 `--consumer-name`：

```text
publication_index_receipt_index_receipt_index_governance_lookup_reader
```

这个改动很小，但很关键。因为真实归档证据来自 CLI，如果 CLI 默认值与 core builder 不一致，测试可能通过，但运行证据会携带旧语义。

## 测试覆盖

单测覆盖：

- ready v1002 review 可以生成 pass receipt。
- summary 中的 receipt status、consumer name、granted use、lookup key count、source evidence count、promotion flag 和 next step 都符合预期。
- requested use 改成 `production_promotion` 会失败。
- source receipt index path 缺失会失败。
- CLI `--require-receipt-ready` 在坏 review 下返回 1，并且仍写出失败报告。
- 输出层覆盖 JSON/CSV/TXT/Markdown/HTML。
- CLI 默认 consumer 被读取回 JSON 并断言，防止 CLI 默认值再次漂移。

收口验证：

```text
focused v1003 tests: 5 passed in 8.04s
source encoding: status=pass, source_count=1874, bom_count=0, syntax_error_count=0, compatibility_error_count=0
git diff --check: pass, only Git line-ending warnings
full pytest: 2387 passed in 455.00s (0:07:35)
```

## 运行证据

运行归档位于 `e/1003`：

- `e/1003/解释/说明.md`
- `e/1003/解释/receipt-v1003/*`
- `e/1003/图片/v1003-receipt.png`

Playwright MCP 截图确认页面展示：

- `Status=pass`
- `Receipt ready=True`
- `Failed=0`
- `Consumer=publication_index_receipt_index_receipt_index_governance_lookup_reader`
- `Use=downstream_governance_lookup_only`

截图说明本版 HTML 证据可浏览、可审阅，且 CLI 默认 consumer 修正已经反映到最终页面。

## 一句话总结

v1003 把 v1002 review 后的 receipt-index-receipt index 推进到“已被治理读者 lookup-only 接收”的状态，同时用检查、测试和截图继续锁住非生产推广边界。

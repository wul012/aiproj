# v1051 publication receipt 代码讲解

## 本版目标和边界

v1051 的目标是把 v1050 reviewed receipt index 记录成 downstream lookup-only receipt。

它解决的问题是：v1050 已经确认 v1049 index 可被 lookup-only receipt recording 消费，但消费动作本身也需要留下 receipt，说明哪个 consumer 读取了哪个 lookup key、获得了什么 use、保留了哪些 source path 和 digest。

本版不做：

- 不训练模型。
- 不新增模型能力评估。
- 不修改 v1050 review 或 v1049 index。
- 不批准 production promotion。
- 不把 receipt_ready 解释为模型质量提升。

## 前置链路

v1051 直接承接：

- v1049：生成 digest-backed receipt index。
- v1050：review v1049 index，确认只允许 lookup-only receipt recording。
- v1051：记录 v1050 review 的 consumer receipt。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1051.py`
  - v1051 receipt builder。
  - 检查 v1050 review 是否 ready，生成 receipt、consumer_receipts、summary 和 check rows。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1051_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 receipt boundary、consumer receipts 和 checks。

- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1051.py`
  - CLI 入口。
  - 支持输入 v1050 review JSON 或目录，支持 `--consumer-name`、`--requested-use`、`--require-receipt-ready`、`--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1051.py`
  - 覆盖 ready receipt、requested use 篡改、source review path 漂移、source evidence status 漂移、CLI failure 和 artifact wiring。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 v1051 receipt next-step 常量，指向 v1051 contract check。

## 核心数据结构

v1051 输出的核心结构是 `receipt`：

- `receipt_ready`
  - 所有 check 通过时为 true。

- `receipt_status`
  - 表达 lookup receipted，不表达 promotion approval。

- `consumer_name`
  - 默认 consumer 是 v1051 lookup reader。

- `requested_use` / `granted_use`
  - 必须保持 `downstream_governance_lookup_only`。

- `receipt_index_review_path` / `receipt_index_review_sha256`
  - 指向 v1050 review，并记录 digest。

- `lookup_keys`
  - 来自 v1050 review 中的 lookup keys。

- `source_receipt_index_path` / `source_receipt_path` / `source_receipt_check_path` / `source_review_path`
  - 保留 v1049、v1047、v1048、v1046 的追溯路径。

- `next_step`
  - ready 时进入 v1051 receipt contract check。

## 检查项说明

`_checks` 保护 25 个关键条件：

- v1050 review file 必须存在。
- v1050 review status/decision/ready key 必须符合 lookup-only review contract。
- requested use 和 granted use 必须保持 downstream lookup-only。
- receipt index lookup 和 contract check 必须 ready。
- receipt index rows 必须为 1。
- source evidence 必须为 2 行，digest 存在且 status pass。
- lookup key 必须来自 source namespace。
- index rows 不允许 promotion。
- review/summary 的 promotion 与 approved-for-promotion 必须为 false。
- consumer boundary 与 model quality claim 必须保持 governance lookup-only / bounded claim。
- v1050 review、v1049 index、v1047 receipt、v1048 check、v1046 review、v1045 index 路径必须仍存在。
- source checks 必须 clean。
- v1050 next_step 必须路由到 receipt recording。

## 输入输出流程

CLI 流程：

1. `locate_receipt_index_review_v1051` 接受 v1050 review JSON 或目录。
2. `read_json_report` 读取 review。
3. builder 抽取 review summary、review body、index rows 和 source evidence。
4. `_checks` 执行 lookup-only/no-promotion/path/digest 检查。
5. `_receipt` 生成 receipt body。
6. `_consumer_receipts` 生成 consumer receipt rows。
7. artifact writer 输出 JSON、CSV、TXT、Markdown、HTML。

## 测试覆盖

聚焦测试验证：

- ready v1050 review 可以生成 receipt。
- requested use 改成 production promotion 会失败。
- source review path 漂移会失败。
- source evidence status 改成 fail 会失败。
- CLI 在坏 review + `--require-receipt-ready` 下返回 1。
- 输出 writer 和 CLI wiring 都可用。

## 运行证据

运行证据归档在：

- `e/1051/解释/receipt-v1051`
- `e/1051/图片/v1051-receipt.png`
- `e/1051/解释/说明.md`

真实 CLI 输出确认：

- `status=pass`
- `receipt_ready=True`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP 快照确认 HTML 页面中 `Status=pass`、`Receipt ready=True`、`Lookup keys=1`、`Evidence=2`、`Use=downstream_governance_lookup_only`、`Failed=0` 和 v1050/v1049/v1047/v1048 source paths 可见。

本地收口验证：

- focused v1051 tests: `6 passed in 0.62s`
- full pytest: `2639 passed in 712.84s`
- source hygiene: `2066/2066 clean`
- py_compile: pass

## 一句话总结

v1051 把 v1050 reviewed receipt index 的消费动作写成 downstream lookup-only receipt，同时继续禁止 promotion。

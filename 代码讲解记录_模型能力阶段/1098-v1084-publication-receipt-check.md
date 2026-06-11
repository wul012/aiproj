# v1084 publication receipt check

## 本版目标

v1084 的目标很窄：对 v1083 receipt 做一次 contract check，确认这份 receipt 是否还能从源 v1082 review 重新推导出来，并且关键字段保持一致。

它解决的是“receipt 产物可能被篡改、源路径可能丢失、lookup-only 边界可能漂移、next_step 可能被错误改写”的问题。

本版不做的事：

- 不训练模型
- 不扩大模型能力结论
- 不新增 promotion 入口
- 不把治理证据包装成模型质量证明

## 路线来源

这一版直接承接 v1083 receipt 和 v1082 review。v1083 已经把 v1082 review 落成 lookup-only receipt；v1084 则反向检查这份 receipt 是否能够被同一套 builder 重建。

所以 v1084 是一个校验层，不是新能力层。它的价值在于让后续索引或审阅模块不用盲信 v1083 JSON，而是可以先确认这份 JSON 仍然能从源证据复原。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1084.py`
  - 核心 contract check。
  - 读取 v1083 receipt，定位源 v1082 review，再调用 v1083 receipt builder 重建 receipt。
  - 对比原始 receipt 与重建 receipt 的关键字段，生成 `issues` 和 `checks`。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1084_artifacts.py`
  - 负责把同一份 check 结果写成 JSON、CSV、TXT、Markdown、HTML。
  - 这些 sidecar 是归档证据，不是训练数据，也不是模型评估结论。

- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1084.py`
  - CLI 入口。
  - 支持输入 receipt JSON 或输出目录，支持 `--out-dir`、`--require-pass`、`--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1084.py`
  - 覆盖正常通过、篡改字段、源路径缺失、digest 漂移和 CLI sidecar 写出。

- `e/1084/解释/receipt-check-v1084/`
  - 保存真实 CLI 运行生成的 JSON/CSV/TXT/MD/HTML。
  - 这是本版的运行证据源。

- `e/1084/图片/v1084-receipt-check.png`
  - Playwright MCP 打开的 HTML 页面截图。
  - 用来证明 HTML 证据页真实可读，且关键字段在页面层可见。

## 核心数据结构

check 结果围绕几个层次组织：

- 顶层 `status` 和 `decision`
  - `status=pass` 表示 contract check 自身通过。
  - 这不表示候选模型被提升，只表示 receipt 与源 review 一致。

- `summary`
  - 保存原始 receipt 与重建 receipt 的关键摘要。
  - 本版重点关注 `original_granted_use`、`rebuilt_granted_use`、`lookup_key_count`、`source_evidence_count`、`promotion_ready`、`next_step`。

- `checks`
  - 每一条都是可审计断言。
  - 例如 status 一致、decision 一致、源 review digest 一致、lookup-only use 一致、source evidence count 一致。

- `issues`
  - 当字段不一致、源路径缺失或 digest 不匹配时写入。
  - 本版真实运行里 `failed_count=0`，所以没有阻断 issue。

## 核心流程

1. CLI 接收 v1083 receipt JSON 或 receipt 输出目录。
2. loader 找到 receipt JSON 并解析。
3. check 模块读取 receipt 中记录的 v1082 review 路径。
4. 调用 v1083 receipt builder，从 v1082 review 重建一份 receipt。
5. 对比原始 receipt 和重建 receipt 的关键字段。
6. 如果所有字段一致，输出 `status=pass` 和 `contract_check_ready=True`。
7. artifact writer 把结果写成多格式 sidecar，供 README、截图和后续索引引用。

## 输入输出格式

输入：

- `e/1083/解释/receipt-v1083/`

输出：

- `e/1084/解释/receipt-check-v1084/*.json`
- `e/1084/解释/receipt-check-v1084/*.csv`
- `e/1084/解释/receipt-check-v1084/*.txt`
- `e/1084/解释/receipt-check-v1084/*.md`
- `e/1084/解释/receipt-check-v1084/*.html`

这些输出都是同一份 check 结果的不同视图。JSON 适合后续程序消费，CSV 适合表格检查，TXT/MD 适合人工阅读，HTML 适合截图归档。

## 测试覆盖

这版测试盯的是 contract，而不是只看 CLI 是否能运行：

- 合法 receipt 能通过，证明重建路径闭合。
- 篡改关键字段会失败，证明原始 receipt 不能随意改写。
- 删除或改错源 review 会失败，证明源路径是必需输入。
- digest 不一致会失败，证明源证据不是只靠路径名称匹配。
- CLI 能写出 sidecar，证明真实运行产物可以归档。

## 运行证据

真实命令输出确认：

- `status=pass`
- `contract_check_ready=True`
- `failed_count=0`
- `original_granted_use=downstream_governance_lookup_only`
- `rebuilt_granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `passed_check_count=46`

Playwright MCP snapshot 确认 HTML 页面显示 `Status pass`、`Contract True`、`Lookup keys 1`、`Failed 0`，并能看到源 review、原始 receipt 状态、重建 receipt 状态和 next-step 路由。

## 验证

- focused v1084 tests：`6 passed in 0.26s`
- full pytest：`2813 passed in 502.09s`
- source hygiene：`2199/2199 clean`
- py_compile：新增模块、artifact writer、CLI、测试均通过。
- `git diff --check` 会在提交前执行。

## 一句话总结

v1084 没有扩大模型能力，而是把 v1083 receipt 的一致性做成可重建、可比较、可截图归档的 contract check。

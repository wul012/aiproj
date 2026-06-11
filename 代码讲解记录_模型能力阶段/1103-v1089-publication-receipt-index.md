# v1089 publication receipt index

## 本版目标

v1089 的目标是把 v1087 记录下来的 lookup-only receipt，以及 v1088 对这份 receipt 做过的 contract check，合并成一份可下游读取的 receipt index。

它解决的问题不是模型变强，而是证据消费方式更稳：下游只读方不需要分别猜测 receipt 和 contract check 的关系，可以通过一份 index 找到两份上游证据、校验它们的 digest、确认 lookup-only 边界，并继续看到 promotion 仍然被阻断。

本版不做的事：

- 不训练新模型。
- 不接受 candidate。
- 不放开 production promotion。
- 不把治理证据解释成模型质量提升。
- 不改写 v1087 或 v1088 的历史产物。

## 路线来源

v1087 已经把 v1086 review 记录成 downstream lookup-only receipt。v1088 又从 v1086 review 重新构建 v1087 receipt，并证明原始 receipt 与 rebuilt receipt 一致。

v1089 接在这两版之后，承担“索引化”的角色：它消费真实的 v1087 receipt 和真实的 v1088 contract check，生成一份带 source evidence digest 的 lookup index。这个模式对应 v1085 的 index 能力，但源头升级到了 v1087/v1088。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1089.py`
  - 核心 builder。
  - 读取 receipt report 和 receipt-check report，执行 25 项 check，并生成 `receipt_index`、`receipt_index_rows`、`source_evidence_rows`、`summary` 和 `interpretation`。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1089_artifacts.py`
  - 负责 JSON/CSV/TXT/Markdown/HTML 输出。
  - HTML 是截图和人工检查入口，JSON 是后续模块消费入口。
- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1089.py`
  - CLI 入口。
  - 支持目录或 JSON 文件作为输入，并提供 `--require-index-ready`、`--require-lookup-ready` 和 `--require-promotion-ready` 退出码约束。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1089.py`
  - 覆盖正常索引、granted use 篡改、contract check 未 ready、CLI 输出和路径定位。
- `e/1089/解释/receipt-index-v1089/`
  - 本版真实运行证据目录。
  - 后续 v1090 review 应消费这里的 JSON 证据。

## 核心数据结构

`receipt_index` 是本版的主结构，关键字段包括：

- `index_ready`
  - 所有 check 通过时为 `True`。
- `receipt_index_id`
  - 本版 index 的稳定标识。
- `lookup_scope`
  - 固定为 `downstream_governance_lookup_only`，说明只能作为治理查找证据。
- `lookup_key_count`
  - 本版期望只有一个 lookup key，避免一份 receipt 扩散成多入口消费。
- `source_evidence_rows`
  - 保存 receipt 和 receipt check 两个源 artifact 的路径、SHA-256 digest 和状态。
- `contract_check_ready`
  - 从 v1088 summary 继承，只在 contract check ready 时为真。
- `promotion_ready`
  - 固定为 `False`，防止 index 产物被误解成放行信号。

`check_rows` 是保护边界的审计清单，覆盖：

- v1087 receipt 文件存在。
- v1088 contract check 文件存在。
- receipt status、decision、summary 和 body 都处于 ready 状态。
- contract check 的 status、decision 和 summary 都通过。
- receipt 与 contract check 中的 receipt status、lookup key count、granted use 和 no-promotion 字段一致。
- v1087 receipt 中记录的上游 review、source receipt、source check、origin index 等路径仍然存在。
- next-step routing 仍然按 `v1087 -> v1088 -> v1089` 串起来。

## 核心流程

1. CLI 定位 v1087 receipt JSON 和 v1088 contract check JSON。
2. builder 读取两个 JSON，并取出 `summary`、`receipt` 与 `check_summary`。
3. `_checks` 执行 25 项断言，确认 receipt、check、上游路径、lookup-only use 和 no-promotion 边界都一致。
4. `_index` 生成一行 receipt index row，并为 receipt 和 receipt check 各生成一行 digest-backed source evidence。
5. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
6. HTML 通过 Playwright MCP 打开并截图，作为运行证据归档。

## 测试覆盖

- 合法 receipt 和 contract check 可以生成 ready index，保护正常链路。
- 篡改 `granted_use` 会失败，保护 downstream lookup-only 边界。
- contract check 不 ready 会失败，防止绕开 v1088。
- CLI 能写出所有 sidecar，并且 `locate_receipt_v1089` 和 `locate_receipt_check_v1089` 能从目录定位 JSON。

这些测试覆盖的是链路契约，不是简单的“脚本能运行”。其中最关键的是：v1089 必须同时相信 receipt 和 receipt check，任何一边不 ready 都不能生成可用 index。

## 运行证据

真实命令消费了：

- `e/1087/解释/receipt-v1087`
- `e/1088/解释/receipt-check-v1088`

输出确认：

- `status=pass`
- `index_ready=True`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP 打开 HTML 后，页面快照能看到 `Receipt Index Rows`、`Source Evidence` 和 `Checks` 三块，截图保存为 `e/1089/图片/v1089-receipt-index.png`。

## 验证

- focused v1089 tests：`4 passed in 0.50s`
- full pytest：`2838 passed in 716.66s`
- source hygiene：`2219/2219 clean`
- py_compile：新增模块、artifact writer、CLI 和测试均通过
- real CLI evidence：生成 JSON/CSV/TXT/Markdown/HTML sidecar
- Playwright MCP screenshot：`e/1089/图片/v1089-receipt-index.png`
- `git diff --check` 在提交前作为收口验证执行

## 一句话总结

v1089 把 v1087 receipt 和 v1088 contract check 从两份分散证据推进成一份 digest-backed lookup index，让后续 review 可以消费一个更完整、更可追溯、仍然不放行 promotion 的证据入口。

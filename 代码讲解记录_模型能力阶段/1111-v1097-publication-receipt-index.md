# v1097 publication receipt index

## 本版目标

v1097 的目标是把 v1095 lookup-only receipt 和 v1096 receipt contract check 放入一个可复核、可检索、带 SHA-256 摘要的 receipt index。这样下一步 review 可以从一个 index artifact 读取 receipt、check、digest、路径和治理边界。

本版解决的是 receipt/check 分散后不易追踪的问题：v1095 证明“下游可以只读消费 v1094 review”，v1096 证明“这个 receipt 可重建且未被篡改”，v1097 则把两份证据合并为下一轮治理链路的 lookup 入口。

本版不做的事：

- 不训练模型。
- 不接受 candidate。
- 不修改 v1095 receipt 或 v1096 contract check。
- 不放开 production promotion。
- 不把治理索引解释成模型能力提升。

## 路线来源

v1093 已经实现过同类 receipt index：它消费 v1091 receipt 和 v1092 contract check，输出 digest-backed lookup evidence。v1097 复用这条模式，只把源头推进到：

- source receipt：v1095
- source receipt check：v1096
- next step：v1097 review

因此 v1093-v1097 形成一轮完整循环：index -> review -> receipt -> contract check -> index。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097.py`
  - v1097 核心 builder。
  - 读取 receipt 和 receipt-check JSON，计算源证据摘要，生成 index rows、source evidence rows、checks 和 summary。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097_artifacts.py`
  - 负责 JSON/CSV/TXT/Markdown/HTML sidecar 输出。
- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097.py`
  - CLI 入口。
  - 支持 receipt/check 的目录或 JSON 文件输入，并通过 `--require-index-ready`、`--require-lookup-ready` 把结果接入自动化 gate。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1097.py`
  - 覆盖合法 index、source digest 篡改、contract check 失败和 CLI 输出。
- `e/1097/解释/receipt-index-v1097/`
  - 本版真实运行证据目录。

## 核心数据结构

`receipt_index` 是本版的中心结构，关键字段包括：

- `receipt_index_id`
  - 本轮 index 的稳定标识。
- `lookup_scope`
  - 固定为 `downstream_governance_lookup_only`，说明它只给后续治理模块查询。
- `lookup_keys`
  - 包含可供下一版 review 使用的 lookup key。
- `rows`
  - 记录 v1095 receipt 的 status、granted use、lookup key count 和 promotion boundary。
- `source_evidence`
  - 记录 v1095 receipt 和 v1096 contract check 的路径、SHA-256、status、decision 和 failed count。
- `checks`
  - 25 项检查结果，保护 source 文件存在、digest 可计算、receipt ready、contract check ready、lookup-only use、no-promotion boundary 和 next-step 路由。
- `summary`
  - 汇总 index 是否 ready、lookup 是否 ready、contract check 是否 ready，以及下一步是否进入 review。

## 核心流程

1. CLI 定位 v1095 receipt JSON 和 v1096 receipt-check JSON。
2. builder 解析两个 source report。
3. `_source_evidence` 计算两份源文件的 SHA-256，并记录路径、status、decision、failed count。
4. `_checks` 验证 receipt ready、contract check pass、digest 非空、lookup-only use、promotion blocked、source next-step 路由一致。
5. `_build_receipt_index` 组装 lookup rows 和 source evidence rows。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML sidecar 并保存截图。

## 测试覆盖

专项测试覆盖 4 个场景：

- 合法 v1095/v1096 输入可以生成 ready index。
- 篡改 source digest 会失败，保护证据内容一致性。
- 把 contract check 改成失败会阻断 index ready，保护防篡改层必须先通过。
- CLI 会生成 sidecar，并在 require 模式下把失败结果传递给退出码。

这些断言让 v1097 不只是“把两个 JSON 拼起来”，而是确认两份上游证据仍然存在、仍然一致、仍然保持 lookup-only 边界。

## 运行证据

真实命令消费：

- `e/1095/解释/receipt-v1095`
- `e/1096/解释/receipt-check-v1096`

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

Playwright MCP 页面快照确认 HTML 中存在 `Receipt Index Rows`、`Source Evidence` 和 `Checks`，截图保存为 `e/1097/图片/v1097-receipt-index.png`。

## 验证

- focused v1097 tests：`4 passed in 0.29s`
- py_compile：新增模块、artifact writer、CLI 和测试均通过
- real CLI evidence：生成 JSON/CSV/TXT/Markdown/HTML sidecar
- Playwright MCP screenshot：`e/1097/图片/v1097-receipt-index.png`
- full pytest：`2880 passed in 651.35s`
- source hygiene：`2251/2251 clean`
- `git diff --check` 在提交前作为收口验证执行

## 一句话总结

v1097 把 v1095 receipt 和 v1096 contract check 从“两个可用证据”推进为“一个可被下一轮 review 消费的 digest-backed lookup index”。

# v1103 publication receipt index

本版目标是把 v1101 lookup-only receipt 和 v1102 contract check 汇总成一个 receipt index，让后续 review 可以从一个入口同时看到 receipt、contract check、source evidence 和 lookup key。

它不训练模型，不接受 candidate，不改写 receipt 或 check，不把 index-ready 解释成 promotion-ready。它只是把已记录和已复核的证据打包成可查询入口。

## 入口

本版入口是 CLI：

```text
scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1103.py
```

核心模块是：

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1103.py
```

CLI 输入 v1101 receipt 和 v1102 receipt check 两个目录或 JSON 文件，输出 JSON/CSV/TXT/Markdown/HTML sidecar。`--require-index-ready` 和 `--require-lookup-ready` 会把 index 或 lookup 不可用转成非零退出码。

## 输出模型

最外层 report 包含：

```text
status
decision
failed_count
issues
receipt_path
receipt_check_path
receipt_index
receipt_index_rows
source_evidence_rows
check_rows
summary
interpretation
```

关键字段是：

```text
index_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
```

`receipt_index_rows` 是下游 lookup 的直接入口，`source_evidence_rows` 保留 receipt/check 两份源文件 digest，让下一步 review 不只依赖路径。

## 上游证据

本版读取真实上游证据：

```text
f/1101/解释/receipt-v1101
f/1102/解释/receipt-check-v1102
```

v1101 证明 v1100 review 已被 lookup-only receipt 记录；v1102 证明该 receipt 可以从 v1100 review 重建。v1103 把两者合并成 index，但不重新执行 receipt builder。

## 核心流程

1. CLI 定位 v1101 receipt JSON 和 v1102 check JSON。
2. builder 读取 receipt summary、receipt body、contract check summary 和 comparison。
3. `_checks` 验证 receipt/check 均通过、receipt/check next step 串联正确、granted use 仍是 lookup-only、source evidence 数量一致、contract check ready、promotion 仍为 false。
4. `_receipt_index` 生成 index body 和 lookup key。
5. `_source_evidence_rows` 写入 receipt/check 的路径、sha256 和状态。
6. artifact writer 输出 JSON/CSV/TXT/Markdown/HTML。
7. Playwright MCP 打开 HTML sidecar 并保存截图到 `f/1103/图片`。

## 关键检查

- `receipt_file_exists` 和 `receipt_check_file_exists`：保护两个上游文件存在。
- `receipt_ready`：保护 v1101 receipt 已 ready。
- `receipt_check_passed` 和 `receipt_check_decision_ready`：保护 v1102 check 已通过。
- `source_next_steps_match`：保护链路是 receipt -> check -> index。
- `lookup_scope_downstream`：保护 index 仍服务 downstream governance lookup。
- `source_evidence_count`：保护两份 source evidence 没丢。
- `contract_check_ready`：保护 index 不绕过 contract check。
- `promotion_still_false`：保护 index 不升级成 production promotion。

## 测试覆盖

专项测试覆盖：

- 合法 receipt/check 可以生成 index。
- check decision 被篡改时失败。
- receipt/check next step 不匹配时失败。
- promotion 被打开时失败。

这些测试保护的是 index 的治理边界和链路顺序，而不是单纯文件存在。

## 运行证据

真实命令消费 `f/1101/解释/receipt-v1101` 和 `f/1102/解释/receipt-check-v1102`，输出确认：

- `status=pass`
- `index_ready=True`
- `lookup_scope=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

验证侧跑了 focused v1103 tests（`4 passed in 0.32s`）、py_compile、source hygiene（`2267/2267 clean`）、`git diff --check` 和真实 CLI。Playwright MCP 页面快照确认 HTML 中存在 `Receipt Index Rows`、`Source Evidence` 和 `Checks`，截图保存为 `f/1103/图片/v1103-receipt-index.png`。

## 链路角色

v1103 位于这一轮链路的 index 位置：

```text
v1095 receipt -> v1096 contract check -> v1097 index -> v1100 review -> v1101 receipt -> v1102 contract check -> v1103 index
```

下一步是 review，不是 promotion。

## 一句话总结

v1103 把 v1101 receipt 和 v1102 contract check 从两份独立证据推进为“可被下一步 review 消费的下游 lookup index”。

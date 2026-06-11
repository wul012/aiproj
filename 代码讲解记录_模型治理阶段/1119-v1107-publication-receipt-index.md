# v1107 publication receipt index

## 本版目标与边界

v1107 的目标是把 v1105 lookup-only receipt 和 v1106 contract check 合并成一份 receipt index。它给后续 review 提供一个稳定的查找入口：哪一份 receipt 被记录、哪一份 contract check 证明它可重建、哪些 source evidence 被绑定、下一步应该进入哪条审阅链路。

本版不训练模型，不新增模型能力断言，不把 `index_ready=True` 解释成 production promotion。它只说明这条治理证据链可以被 lookup 和 review，仍然禁止把 candidate 当作可上线模型使用。

## 前置路线

v1107 承接：

```text
v1104 review -> v1105 receipt -> v1106 contract check -> v1107 index
```

v1105 记录了 v1104 review，v1106 证明 v1105 receipt 可以从 v1104 review 重建。v1107 负责把 receipt 与 check 打包为一个可查询索引，供 v1108 review 使用。

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107.py
```

核心 index builder，负责读取 receipt 与 receipt-check report，生成 lookup row、source evidence rows、checks、summary 和 interpretation。

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107_artifacts.py
```

artifact writer，负责输出 JSON、CSV、TXT、Markdown、HTML。JSON 是后续 review 的输入，HTML/Markdown 是人工审阅面。

```text
scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107.py
```

CLI 入口，要求显式传入 `--receipt` 和 `--receipt-check`。`--require-index-ready` 和 `--require-lookup-ready` 可以把失败转成非零退出码。

```text
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107.py
```

专项测试，验证合法 index、缺失 check、篡改 lookup scope、CLI gating 和 artifact 输出。

## 入口与参数

真实运行命令：

```powershell
python -B scripts\build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107.py --receipt f\1105\解释\receipt-v1105 --receipt-check f\1106\解释\receipt-check-v1106 --out-dir f\1107\解释\receipt-index-v1107 --require-index-ready --require-lookup-ready --force
```

输入分为两类：

- `--receipt`：v1105 lookup-only receipt JSON 或输出目录。
- `--receipt-check`：v1106 contract-check JSON 或输出目录。

这两个输入必须同时存在，因为 index 不只保存 receipt 本身，还要保存它已经被 contract check 复核过的证据。

## 输出模型

v1107 report 包含：

```text
status
decision
failed_count
issues
receipt_index
source_receipt
source_receipt_check
check_rows
summary
interpretation
```

`receipt_index` 是核心结构，里面包含：

```text
index_id
lookup_scope
lookup_rows
source_evidence
contract_check
promotion_boundary
```

其中 `lookup_rows` 是后续 review 和下游查找的最小行；`source_evidence` 说明该行来自 v1105 receipt 和 v1106 check；`promotion_boundary` 明确保留 `promotion_ready=False`。

`summary` 给后续模块稳定读取：

```text
index_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
next_step=review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1107
```

## 上游证据

本版读取：

```text
f/1105/解释/receipt-v1105
f/1106/解释/receipt-check-v1106
```

v1105 receipt 证明 v1104 review 已被记录为 lookup-only receipt。v1106 contract check 证明这份 receipt 能从 v1104 review 重建。v1107 同时消费二者，防止出现“有 receipt 但没有 check”或“check 指向另一份 receipt”的漂移。

## 核心流程

1. CLI 定位 v1105 receipt JSON。
2. CLI 定位 v1106 receipt-check JSON。
3. builder 读取 receipt summary、receipt body、check summary 和 check comparison。
4. builder 生成单条 lookup row，保存 receipt id/status、granted use、lookup key 和 source path。
5. builder 生成 source evidence rows，分别绑定 receipt 与 contract check。
6. `_checks` 验证 receipt 通过、check 通过、lookup scope 正确、lookup key 数量为 1、source evidence 数量为 2、promotion 没有打开。
7. artifact writer 生成 JSON/CSV/TXT/Markdown/HTML。
8. Playwright MCP 打开 HTML 并截图，确认人工审阅区块可见。

## 关键检查

- `receipt_passed`：保护 v1105 receipt 本身是 pass。
- `receipt_check_passed`：保护 v1106 contract check 是 pass。
- `receipt_check_ready`：保护 check 不是空壳。
- `lookup_scope_matches`：保护 index 仍是 `downstream_governance_lookup_only`。
- `lookup_key_count_is_one`：保护查找入口没有丢失或重复膨胀。
- `source_evidence_count_is_two`：保护 receipt 和 check 两类来源都被保留。
- `contract_check_ready`：保护 index 包含可复核的 check 链接。
- `promotion_ready_false`：保护 index 不会把治理证据升级成上线许可。

这些检查让 v1107 成为可审阅索引，而不是简单的文件清单。

## 测试覆盖

focused tests 覆盖：

- 合法 receipt + check 可以生成 ready index。
- 缺失或失败 check 会阻断 index。
- 篡改 lookup scope 会失败。
- CLI `--require-index-ready` 和 `--require-lookup-ready` 能正确返回退出码。
- artifact writer 生成完整 sidecar。

测试重点是保护 receipt 与 check 的配对关系，以及 lookup-only/no-promotion 边界。

## 运行证据

真实 CLI 输出确认：

```text
status=pass
index_ready=True
lookup_scope=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

验证包括 py_compile、focused v1107 tests（`4 passed in 0.56s`）、source hygiene（`2283/2283 clean`）、真实 CLI、`git diff --check` 和 Playwright MCP 截图。

截图保存到：

```text
f/1107/图片/v1107-receipt-index.png
```

页面快照确认 `Receipt Index Rows`、`Source Evidence` 和 `Checks` 都可见。

## 链路角色

v1107 位于 contract check 之后、review 之前。它让后续 v1108 不必分别追踪 receipt/check 两份文件，而是读取一个统一 index；同时它保留了 `promotion_ready=False`，避免 lookup-ready 被误读为 production-ready。

## 一句话总结

v1107 把 v1105 receipt 与 v1106 contract check 合并为 lookup-only、可审阅、可阻断的 receipt index。

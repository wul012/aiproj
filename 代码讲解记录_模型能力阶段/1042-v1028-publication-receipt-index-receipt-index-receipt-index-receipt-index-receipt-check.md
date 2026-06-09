# v1028 publication receipt index receipt index receipt index receipt index receipt check 代码讲解

## 本版目标和边界

v1028 的目标是 contract-check v1027 downstream lookup-only receipt，确认它能从 v1026 review 重新构建。

它解决的问题是：v1027 receipt 记录了下游 lookup reader 的消费行为，但 receipt artifact 如果被手动改动，后续 index 会把错误内容继续传播。v1028 用源 review 重建 receipt，并对原始结果和 rebuilt 结果做字段级比较。

本版不做模型训练，不改变 holdout 评估，不证明模型能力提升，也不开放 production promotion。

## 前置能力

v1027 生成了：

```text
e/1027/解释/receipt-v1027/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json
```

该 receipt 内部指向 v1026 review：

```text
e/1026/解释/receipt-index-review-v1026/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json
```

v1028 不信任 v1027 的最终字段，而是读取这个源 review，再调用 v1027 builder 重新生成一份 receipt。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.py`
  - v1028 contract-check 核心模块。
  - 负责定位源 review、重建 receipt、比较原始/rebuilt 字段。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1028.py`
  - 命令行入口。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.py`
  - 覆盖通过路径、篡改失败路径、路径失败路径、digest 失败路径和 CLI 输出。
- `e/1028/解释/receipt-check-v1028/`
  - 真实运行产物。
- `e/1028/图片/v1028-receipt-check.png`
  - Playwright MCP 截图证据。

## 核心数据结构

本版报告包含两组关键对象：

```text
original_summary
rebuilt_summary
original_receipt
rebuilt_receipt
check_rows
summary
interpretation
```

`original_*` 来自 v1027 artifact。`rebuilt_*` 来自重新读取 v1026 review 并调用 v1027 builder 的结果。

`summary` 是下游最常读的摘要：

```text
contract_check_ready
source_receipt_index_review
original_receipt_status
rebuilt_receipt_status
original_granted_use
rebuilt_granted_use
original_lookup_key_count
rebuilt_lookup_key_count
original_promotion_ready
rebuilt_promotion_ready
next_step
passed_check_count
failed_check_count
```

其中 `next_step` 指向：

```text
index_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1028
```

这表示 contract check 通过后，可以把 v1027 receipt 与 v1028 check 一起进入下一版 index。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028(...)` 是主入口。

它的流程是：

1. 从 v1027 receipt 读取 `summary` 和 `receipt`。
2. 调用 `_resolve_source_review_path(...)` 找到 `receipt_index_review_path`。
3. 调用 `_rebuild_receipt(...)` 读取 v1026 review，并调用 v1027 receipt builder 重建 receipt。
4. 调用 `_checks(...)` 比较原始结果和 rebuilt 结果。
5. 汇总 `contract_check_ready`、check 数量和 next step。

`_checks(...)` 先做六个整体检查：

- source review 文件存在；
- status 可重建一致；
- decision 可重建一致；
- failed count 可重建一致；
- source review SHA-256 可重建一致；
- consumer receipts 可重建一致。

随后 `_field_checks(...)` 分别比较 `SUMMARY_FIELDS` 和 `RECEIPT_FIELDS`。

`SUMMARY_FIELDS` 覆盖：

- ready key；
- receipt id/type/status；
- consumer name；
- granted use；
- row/evidence/lookup key count；
- promotion flags；
- consumer boundary；
- model quality claim；
- next step；
- passed/failed check count。

`RECEIPT_FIELDS` 覆盖更细的 source path、source digest、review status 和 lookup keys。

## CLI 流程

真实运行命令：

```text
python scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1028.py e/1027/解释/receipt-v1027 --out-dir e/1028/解释/receipt-check-v1028 --require-pass --force
```

CLI 支持传目录，locator 会自动找到：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json
```

`--require-pass` 让 contract check 失败时返回非零状态，适合后续 CI 或自动化消费。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1028_passed
contract_check_ready=True
original_receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted
rebuilt_receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_lookup_key_count=1
rebuilt_lookup_key_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

HTML 报告截图保存到：

```text
e/1028/图片/v1028-receipt-check.png
```

## 测试覆盖

focused 测试覆盖六条路径：

- rebuildable v1027 receipt 可以通过 contract check；
- `granted_use` 被改成 `production_promotion` 会失败；
- source review 缺失会失败；
- source review digest 被篡改会失败；
- `--require-pass` 对失败输入返回非零；
- CLI 可以从目录定位输入并写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
6 passed in 21.52s
```

全量回归结果：

```text
2519 passed in 594.82s
```

source encoding hygiene 结果：

```text
source_count=1974
clean_count=1974
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1028 让 v1027 lookup-only receipt 具备可重建的 contract-check 证明，但仍然没有把治理链条解释为生产模型能力。

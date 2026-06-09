# v1029 publication receipt index receipt index receipt index receipt index receipt index 代码讲解

## 本版目标和边界

v1029 的目标是把 v1027 lookup-only receipt 与 v1028 contract check 合并成 digest-backed receipt index。

它解决的问题是：receipt 已经可记录，contract check 已经证明它能重建，但后续 review 和 lookup 不应该同时追两个零散文件。v1029 提供一个统一索引，记录 lookup key、receipt id、receipt/check 路径、SHA-256 和 no-promotion 边界。

本版不做模型训练，不改变 holdout 评估，不证明模型能力提升，也不开放 production promotion。

## 前置能力

v1027 生成了 downstream receipt：

```text
e/1027/解释/receipt-v1027/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json
```

v1028 生成了 contract check：

```text
e/1028/解释/receipt-check-v1028/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json
```

v1029 不重新构建 receipt，也不重新执行 contract check；它只验证这两个输入仍满足 index 条件。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029.py`
  - v1029 receipt index 核心模块。
  - 负责校验 receipt/check、生成 lookup row 和 source evidence rows。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029.py`
  - 命令行入口。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029.py`
  - 覆盖通过路径、篡改失败路径、contract check 失败路径和 CLI 输出。
- `e/1029/解释/receipt-index-v1029/`
  - 真实运行产物。
- `e/1029/图片/v1029-receipt-index.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`receipt_index` 是本版核心输出对象：

```text
index_ready
receipt_index_id
lookup_scope
lookup_key_count
receipt_index_rows
source_evidence_rows
source_evidence_count
receipt_path
receipt_check_path
receipt_id
receipt_status
granted_use
lookup_ready
contract_check_ready
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
source_next_step
next_step
```

`receipt_index_rows` 当前只有一行。它包含：

```text
receipt_index_id
lookup_key
receipt_id
receipt_status
granted_use
source_receipt_path
source_receipt_check_path
source_review_path
source_receipt_index_path
contract_check_ready
promotion_ready
```

`source_evidence_rows` 当前两行：

- `kind=receipt`：指向 v1027 receipt；
- `kind=receipt_check`：指向 v1028 contract check。

两行都记录 `path`、`sha256` 和 `status`。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029(...)` 是主入口。

它的流程是：

1. 读取 v1027 receipt 的 `summary` 和 `receipt`。
2. 读取 v1028 check 的 `summary`。
3. 调用 `_checks(...)` 验证 receipt/check 是否可进入 index。
4. 调用 `_index(...)` 生成 lookup row 与 evidence rows。
5. 生成摘要、interpretation 和 artifact-friendly report。

`_checks(...)` 保护以下条件：

- receipt 文件存在；
- receipt check 文件存在；
- receipt status/decision/ready 字段正确；
- receipt check status/decision/contract ready 字段正确；
- receipt status 与 contract check 的 original/rebuilt status 一致；
- granted use 全链路仍为 downstream lookup only；
- lookup key 数量仍然是 1；
- source evidence 数量仍然是 2；
- source review、source index、source receipt、source check 等路径仍存在；
- consumer boundary 与 model quality claim 仍然受限；
- promotion flags 全部为 false；
- source receipt/check 的 failed check count 都是 0；
- source next step 保持 receipt -> check -> index 的顺序。

## CLI 流程

真实运行命令：

```text
python scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029.py --receipt e/1027/解释/receipt-v1027 --receipt-check e/1028/解释/receipt-check-v1028 --out-dir e/1029/解释/receipt-index-v1029 --require-index-ready --require-lookup-ready --force
```

CLI 支持传目录，locator 会自动找到：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.json
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1028.json
```

`--require-index-ready` 和 `--require-lookup-ready` 让 index 不通过时返回非零状态，适合后续 CI 或自动化消费。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1029_ready
index_ready=True
receipt_index_id=randomized-holdout-publication-receipt-index-receipt-index-receipt-index-receipt-index-receipt-index-v1029
lookup_scope=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

HTML 报告截图保存到：

```text
e/1029/图片/v1029-receipt-index.png
```

## 测试覆盖

focused 测试覆盖四条路径：

- ready receipt/check 可以生成 index；
- `granted_use` 改成 `production_promotion` 会失败；
- contract check 不 ready 会失败；
- CLI 可以从目录定位输入并写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
4 passed in 6.43s
```

全量回归结果：

```text
2523 passed in 449.99s
```

source encoding hygiene 结果：

```text
source_count=1978
clean_count=1978
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1029 把 lookup-only receipt 与其 contract check 收束成 digest-backed index，为下一步 review 提供单一、可校验入口。

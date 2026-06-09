# v1036 publication receipt index receipt index receipt index receipt index receipt index receipt index receipt check 代码讲解

## 本版目标和边界

v1036 的目标是对 v1035 downstream lookup-only receipt 做 contract check。

它解决的问题是：v1035 receipt 已经记录了 v1034 review 的消费许可，但下游继续索引前还需要确认 receipt 没有漂移。v1036 读取 v1035 receipt，回到它记录的 `receipt_index_review_path`，从 v1034 review 重新构建 receipt，然后逐项比较原始 receipt 与重建 receipt。

本版不做模型训练，不改变模型评价，不批准生产推广。它只验证 receipt contract 的可重建性。

## 前置能力

v1035 输出：

```text
e/1035/解释/receipt-v1035/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035.json
```

该 receipt 包含：

- v1034 review 路径；
- v1034 review SHA-256；
- 1 条 consumer receipt；
- 1 个 lookup key；
- `granted_use=downstream_governance_lookup_only`；
- `promotion_ready=False`；
- `approved_for_promotion=False`。

v1036 只验证这份 receipt 是否可重建，不重新判定模型是否可发布。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036.py`
  - v1036 contract-check 核心模块。
  - 从 v1035 receipt 定位 v1034 review，重建 receipt，并逐字段比较。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1036.py`
  - CLI 入口。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036.py`
  - 覆盖 ready、granted use 篡改、source review 缺失、source digest 篡改、CLI require 失败和 artifact 输出。
- `e/1036/解释/receipt-check-v1036/`
  - 真实运行产物。
- `e/1036/图片/v1036-receipt-check.png`
  - Playwright MCP 截图证据。

## 核心数据结构

v1036 输出里最重要的是三组字段：

```text
original_summary
rebuilt_summary
check_rows
```

`original_summary` 来自 v1035 JSON。

`rebuilt_summary` 来自重新调用 v1035 builder 的结果。

`check_rows` 保存每个字段的 contract check 结果。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1036(...)` 是主入口。

它执行四步：

1. 读取原始 v1035 receipt。
2. 从 `receipt_index_review_path` 定位 v1034 review。
3. 调用 v1035 builder 从 v1034 review 重建 receipt。
4. 比较原始与重建产物。

比较范围包括：

- `status`
- `decision`
- `failed_count`
- `receipt_index_review_sha256`
- `consumer_receipts`
- summary 字段
- receipt 字段

summary 字段包括：

```text
receipt_ready
receipt_id
receipt_type
receipt_status
consumer_name
granted_use
receipt_index_row_count
source_evidence_count
lookup_key_count
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
next_step
passed_check_count
failed_check_count
```

receipt 字段包括 source path、digest、lookup keys、review status、promotion boundary 和 next step。

## CLI 流程

真实运行命令：

```text
python scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1036.py e/1035/解释/receipt-v1035 --out-dir e/1036/解释/receipt-check-v1036 --require-pass --force
```

目录输入会自动定位：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035.json
```

`--require-pass` 表示只要 contract check 失败，CLI 就返回非 0。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1036_passed
contract_check_ready=True
original_receipt_status=rebuilt_receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035_lookup_receipted
original_granted_use=rebuilt_granted_use=downstream_governance_lookup_only
original_lookup_key_count=rebuilt_lookup_key_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

HTML 报告截图保存到：

```text
e/1036/图片/v1036-receipt-check.png
```

## 测试覆盖

focused 测试覆盖六条路径：

- rebuildable v1035 receipt 可以通过；
- summary/receipt 的 `granted_use` 被改成 production promotion 会失败；
- source review 路径缺失会失败；
- source review digest 被篡改会失败；
- CLI `--require-pass` 对坏 receipt 返回 `1`；
- artifact writer 和 CLI 都能写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
6 passed in 11.73s
```

全量回归结果：

```text
2561 passed in 530.81s
```

source encoding hygiene 结果：

```text
source_count=2006
clean_count=2006
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1036 把 v1035 receipt 从“已记录”推进到“可重建、可审计、可继续索引”的状态，同时仍然保持 no-promotion 边界。

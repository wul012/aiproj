# v1032 publication receipt index receipt index receipt index receipt index receipt index receipt check 代码讲解

## 本版目标和边界

v1032 的目标是对 v1031 downstream lookup-only receipt 做重建式 contract check。

它解决的问题是：v1031 生成了 receipt artifact，但 artifact 本身不能只靠“存在”来被信任。v1032 从 receipt 内的 `receipt_index_review_path` 找回 v1030 review，重新构建 receipt，并比较 original/rebuilt 的稳定字段，确认 v1031 没有漂移或被篡改。

本版不做模型训练，不变更 baseline/candidate，不开放 production promotion。

## 前置能力

v1031 输出了：

```text
e/1031/解释/receipt-v1031/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031.json
```

该 receipt 已记录：

- `receipt_ready=True`；
- `granted_use=downstream_governance_lookup_only`；
- `receipt_index_review_path` 指向 v1030 review；
- `lookup_key_count=1`；
- `source_evidence_count=2`；
- `promotion_ready=False`。

v1032 只验证这份 receipt 是否能从 v1030 review 重建出来。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1032.py`
  - v1032 contract check 核心模块。
  - 读取 v1031 receipt，定位 v1030 review，重建 receipt，并比较字段。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1032_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1032.py`
  - CLI 入口。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1032.py`
  - 覆盖通过路径、篡改 use、source review 缺失、digest 篡改、CLI fail-fast 和 artifact 输出。
- `e/1032/解释/receipt-check-v1032/`
  - 真实运行产物。
- `e/1032/图片/v1032-receipt-check.png`
  - Playwright MCP 截图证据。

## 核心数据结构

本版输出包含四组关键对象：

```text
original_summary
rebuilt_summary
original_receipt
rebuilt_receipt
```

`SUMMARY_FIELDS` 用于比较 summary 层稳定字段：

```text
receipt_ready key
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

`RECEIPT_FIELDS` 用于比较 receipt body：

```text
receipt_ready
receipt_id
receipt_type
receipt_status
consumer_name
requested_use
granted_use
receipt_index_review_path
receipt_index_review_sha256
receipt_index_row_count
source_evidence_count
lookup_keys
review_id
review_status
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
source_receipt_index_path
source_receipt_path
source_receipt_check_path
source_review_path
source_receipt_index_origin_path
next_step
```

这些字段都是下游判断 receipt 是否可信、是否仍然 lookup-only、是否仍然禁止 promotion 的关键证据。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1032(...)` 是主入口。

它的流程是：

1. 从 v1031 receipt 读取 `original_summary` 和 `original_receipt`。
2. 用 `_resolve_source_review_path(...)` 找到 v1030 review。
3. 用 `_rebuild_receipt(...)` 重新调用 v1031 builder。
4. 用 `_checks(...)` 比较 original 与 rebuilt。
5. 输出 contract check summary。

`_checks(...)` 保护以下条件：

- source review 文件存在；
- original/rebuilt `status` 一致；
- original/rebuilt `decision` 一致；
- original/rebuilt `failed_count` 一致；
- `receipt_index_review_sha256` 一致；
- `consumer_receipts` 完全一致；
- summary 字段逐项一致；
- receipt body 字段逐项一致。

通过后，`contract_check_ready=True`。失败时，`--require-pass` 会让 CLI 返回非零状态。

## CLI 流程

真实运行命令：

```text
python scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1032.py e/1031/解释/receipt-v1031 --out-dir e/1032/解释/receipt-check-v1032 --require-pass --force
```

CLI 支持传入 receipt JSON 或 receipt 输出目录。目录输入会自动定位：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031.json
```

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1032_passed
contract_check_ready=True
original_receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_lookup_receipted
rebuilt_receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_lookup_receipted
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
e/1032/图片/v1032-receipt-check.png
```

## 测试覆盖

focused 测试覆盖六条路径：

- 可重建的 v1031 receipt 通过 contract check；
- `granted_use` 被篡改会失败；
- source review 缺失会失败；
- source digest 被篡改会失败；
- CLI 在坏 receipt + `--require-pass` 下返回 1；
- artifact writer 和 CLI 都能写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
6 passed in 12.20s
```

全量回归结果：

```text
2540 passed in 867.64s
```

source encoding hygiene 结果：

```text
source_count=1990
clean_count=1990
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1032 把 v1031 receipt 从“已生成”推进到“可从源 review 重建验证”，让下游 lookup-only 消费更可信，但仍不触发模型生产晋级。

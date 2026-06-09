# v1039 publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index receipt 代码讲解

## 本版目标和边界

v1039 的目标是把 v1038 审查通过的 receipt index 记录成一个 downstream governance lookup-only receipt。

前一版 v1038 已经确认 v1037 digest-backed receipt index 可以被下游治理查询消费。v1039 不重新计算 index，也不重新审查 v1035/v1036 的底层产物，而是记录一个新的消费收据：说明下游 consumer 可以 lookup 哪个 key、授权用途是什么、源 review/index/receipt/check 是否仍然可追溯。

本版不训练模型，不改变 tokenizer/model/checkpoint，不把随机 holdout 的 bounded claim 扩大成生产能力声明，也不批准 production promotion。

## 前置链路

v1039 依赖 v1038 的真实 review 输出：

```text
e/1038/解释/receipt-index-review-v1038/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038.json
```

该 review 又指向：

- v1037 receipt index；
- v1035 lookup-only receipt；
- v1036 receipt contract check；
- v1034 source review；
- v1033 source index。

因此 v1039 的定位是“已审查索引的下游消费收据”，不是新一轮模型评估。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039.py`
  - v1039 核心 builder。
  - 输入 v1038 review JSON，输出 receipt、summary、check rows 和 consumer receipts。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - HTML 是运行截图的直接页面，不是额外解释层。
- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039.py`
  - CLI 入口。
  - 支持目录输入，自动定位 v1038 review JSON。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039.py`
  - 覆盖 ready receipt、requested use 篡改、source review path 漂移、source evidence status 篡改、CLI failure exit 和 artifact 输出。
- `e/1039/解释/receipt-v1039/`
  - 真实运行产物。
- `e/1039/图片/v1039-receipt.png`
  - Playwright MCP 截图证据。

## 核心数据结构

v1039 的主输出包含：

```text
receipt
consumer_receipts
summary
check_rows
```

`receipt` 是核心收据体，包含：

- `receipt_ready`
- `receipt_id`
- `receipt_type`
- `receipt_status`
- `consumer_name`
- `requested_use`
- `granted_use`
- `receipt_index_review_path`
- `receipt_index_review_sha256`
- `receipt_index_row_count`
- `source_evidence_count`
- `lookup_keys`
- `review_id`
- `review_status`
- `promotion_ready`
- `approved_for_promotion`
- `source_receipt_index_path`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_origin_path`
- `next_step`

`consumer_receipts` 把 lookup key、source receipt、receipt id 和 granted use 展平成下游可读行。后续模块不需要重新解析整份 review，即可知道“这个 consumer 被允许 lookup 什么”。

`summary` 是 CLI、README 和 contract check 最常用的摘要层，稳定暴露 `receipt_ready`、`receipt_status`、`lookup_key_count`、`source_evidence_count`、`promotion_ready`、`passed_check_count` 和 `failed_check_count`。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039(...)` 是主入口。

它的运行流程是：

1. 从 v1038 review 中读取 `summary`、`review`、`receipt_index_rows` 和 `source_evidence_rows`。
2. 调用 `_checks(...)` 检查 review 是否通过、decision 是否 ready、lookup-only 授权是否保持、source evidence 是否仍然 pass、源文件路径是否存在、promotion 是否仍然 false。
3. 如果所有检查通过，调用 `_receipt(...)` 生成 lookup-only receipt。
4. 调用 `_consumer_receipts(...)` 生成下游消费行。
5. 调用 `_summary(...)` 和 `_interpretation(...)` 输出人类和机器都容易读取的结论。

关键检查包括：

- `receipt_index_review_file_exists`
- `receipt_index_review_passed`
- `receipt_index_review_decision_ready`
- `review_status_allowed`
- `requested_use_allowed`
- `lookup_only_granted_use`
- `receipt_index_lookup_ready`
- `contract_check_ready`
- `source_evidence_digests_present`
- `source_evidence_status_pass`
- `lookup_keys_source_namespace`
- `source_receipt_index_file_exists`
- `source_receipt_file_exists`
- `source_receipt_check_file_exists`
- `source_review_file_exists`
- `source_next_step_matches`

这些检查共同保护一个边界：v1039 可以记录 lookup-only receipt，但不能把 receipt index 解释成生产推广许可。

## CLI 流程

真实运行命令：

```text
python scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1039.py e/1038/解释/receipt-index-review-v1038 --out-dir e/1039/解释/receipt-v1039 --require-receipt-ready --force
```

目录输入会自动定位：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038.json
```

本次真实输出：

```text
status=pass
receipt_ready=True
lookup_key_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

`--require-receipt-ready` 使 CLI 在 receipt 未 ready 时返回非零状态。测试里专门篡改 `lookup_ready`，确认失败时确实会返回 `1`。

## 测试覆盖

focused test 包含 6 个测试：

- ready review 可以生成 pass receipt；
- `requested_use=production_promotion` 会失败；
- source review path 漂移会失败；
- source evidence status 从 pass 改成 fail 会失败；
- `--require-receipt-ready` 对坏 review 返回 `1`；
- artifact 写出和 CLI 目录输入都可用。

这组测试保护的是 v1039 的收据边界，而不是 UI 文案。

## 运行证据

运行证据位于：

```text
e/1039/解释/receipt-v1039/
e/1039/图片/v1039-receipt.png
```

Playwright MCP 快照确认页面展示：

- `Status=pass`；
- `Receipt ready=True`；
- `Failed=0`；
- v1038 source review；
- v1037 source receipt index；
- v1035 source receipt；
- v1036 source check；
- v1039 next step。

## 一句话总结

v1039 把 v1038 审查过的 receipt index 变成可追溯的 downstream lookup-only receipt，同时继续把模型质量声明和生产推广锁在治理边界之外。

# v1038 publication receipt index receipt index receipt index receipt index receipt index receipt index receipt index review 代码讲解

## 本版目标和边界

v1038 的目标是审查 v1037 digest-backed receipt index，确认它可以进入下一步 lookup-only receipt recording。

v1037 已经把 v1035 receipt 和 v1036 contract check 收束成一个索引。v1038 不再重新构造 receipt/check，而是检查这份索引本身是否仍然满足：文件存在、lookup key 命名空间正确、source evidence digest 存在、contract check ready、bounded claim 不变、promotion 仍然为 false。

本版不训练模型，不改变模型能力评价，不批准 production promotion。它只审查 receipt index 的消费边界。

## 前置能力

v1037 输出：

```text
e/1037/解释/receipt-index-v1037/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037.json
```

该索引包含：

- 1 条 receipt index row；
- 1 个 lookup key；
- 2 条 source evidence；
- v1035 receipt path；
- v1036 receipt contract check path；
- `lookup_scope=downstream_governance_lookup_only`；
- `promotion_ready=False`。

v1038 的角色是确认这些字段可以被后续 receipt recording 可信消费。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038.py`
  - v1038 review 核心模块。
  - 读取 v1037 receipt index，生成 lookup-only review。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1038.py`
  - CLI 入口。
  - 支持目录输入，自动定位 v1037 index JSON。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038.py`
  - 覆盖 ready review、granted use 篡改、source evidence digest 缺失、source path 漂移和 CLI/artifact 输出。
- `e/1038/解释/receipt-index-review-v1038/`
  - 真实运行产物。
- `e/1038/图片/v1038-receipt-index-review.png`
  - Playwright MCP 截图证据。

## 核心数据结构

v1038 输出的核心是：

```text
review
summary
check_rows
```

`review` 保存审查结论：

- `review_ready`
- `review_id`
- `review_status`
- `receipt_index_path`
- `receipt_index_id`
- `receipt_index_row_count`
- `lookup_keys`
- `source_evidence_count`
- `lookup_ready`
- `contract_check_ready`
- `promotion_ready`
- `approved_for_promotion`
- `next_step`

`summary` 将 review 里的关键字段提平，方便 CLI、README 和后续 receipt builder 读取。

`check_rows` 列出 22 条检查结果，是本版最重要的审计证据。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038(...)` 是主入口。

它执行五步：

1. 读取 v1037 index 的 `summary` 和 `receipt_index`。
2. 读取 `receipt_index_rows` 和 `source_evidence_rows`。
3. 调用 `_checks(...)` 校验源文件、source evidence、lookup namespace、contract readiness、bounded claim 和 no-promotion 字段。
4. 调用 `_review(...)` 生成 lookup-only review。
5. 调用 `_summary(...)` 和 `_interpretation(...)` 暴露下游可读结论。

关键检查包括：

- `receipt_index_file_exists`
- `receipt_index_passed`
- `receipt_index_decision_ready`
- `receipt_index_summary_ready`
- `lookup_scope_downstream`
- `granted_use_lookup_only`
- `lookup_ready`
- `contract_check_ready`
- `source_evidence_digests_present`
- `source_receipt_file_exists`
- `source_receipt_check_file_exists`
- `promotion_still_false`
- `source_next_step_matches`

这些检查保证 v1038 只批准 lookup-only receipt recording，不把 v1037 的索引误解成生产推广许可。

## CLI 流程

真实运行命令：

```text
python scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1038.py e/1037/解释/receipt-index-v1037 --out-dir e/1038/解释/receipt-index-review-v1038 --require-review-ready --require-lookup-ready --force
```

目录输入会自动定位：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1037.json
```

`--require-review-ready` 要求 review 结构通过。

`--require-lookup-ready` 要求 lookup key 可用于下游。

`--require-promotion-ready` 仍然会失败，因为 promotion 不是本链路允许的目标。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1038_ready
review_ready=True
review_status=approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only
receipt_index_row_count=1
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=22
failed_check_count=0
```

HTML 报告截图保存到：

```text
e/1038/图片/v1038-receipt-index-review.png
```

## 测试覆盖

focused 测试覆盖五条路径：

- ready v1037 index 可以通过 review；
- `granted_use` 被改成 production promotion 会失败；
- source evidence digest 缺失会失败；
- source receipt path 漂移会失败；
- artifact writer 和 CLI 都能写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
5 passed in 8.00s
```

全量回归结果：

```text
2570 passed in 564.73s
```

source encoding hygiene 结果：

```text
source_count=2014
clean_count=2014
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1038 把 v1037 digest-backed index 从“已收束”推进到“可被 lookup-only receipt recording 消费”的状态，继续维持 no-promotion 边界。

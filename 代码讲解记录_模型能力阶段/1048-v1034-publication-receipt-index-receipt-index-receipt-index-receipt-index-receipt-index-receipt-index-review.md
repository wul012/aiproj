# v1034 publication receipt index receipt index receipt index receipt index receipt index receipt index review 代码讲解

## 本版目标和边界

v1034 的目标是审查 v1033 digest-backed receipt index，确认它能作为下一步 lookup-only receipt recording 的输入。

它解决的问题是：v1033 已经把 v1031 receipt 和 v1032 check 编成索引，但下游不应直接信任索引本身。v1034 重新检查 index readiness、lookup scope、source evidence、source paths、bounded claim 和 no-promotion 字段。

本版不做模型训练，不改变模型评估结果，不批准生产推广。

## 前置能力

v1033 输出：

```text
e/1033/解释/receipt-index-v1033/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1033.json
```

该 index 包含：

- 1 条 `receipt_index_rows`；
- 2 条 `source_evidence_rows`；
- v1031 receipt 路径；
- v1032 contract check 路径；
- `lookup_ready=True`；
- `contract_check_ready=True`；
- `promotion_ready=False`。

v1034 只审查这份 index，不重建 v1031 receipt 或 v1032 check。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1034.py`
  - v1034 review 核心模块。
  - 检查 v1033 index 是否满足下一步 receipt recording 条件。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1034_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1034.py`
  - CLI 入口。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1034.py`
  - 覆盖 ready、granted use 漂移、digest 缺失、source path 漂移、CLI/artifact 输出。
- `e/1034/解释/receipt-index-review-v1034/`
  - 真实运行产物。
- `e/1034/图片/v1034-receipt-index-review.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`review` 是核心输出：

```text
review_ready
review_id
review_status
receipt_index_path
receipt_index_id
receipt_index_row_count
lookup_keys
source_evidence_count
lookup_ready
contract_check_ready
granted_use
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
source_receipt_path
source_receipt_check_path
source_review_path
source_receipt_index_path
next_step
```

`review_status` 固定为：

```text
approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only
```

这表示“允许进入 lookup-only receipt recording”，不是生产发布批准。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1034(...)` 是主入口。

它读取 v1033 index 后，提取：

- `index_summary`
- `receipt_index`
- `receipt_index_rows`
- `source_evidence_rows`

然后调用 `_checks(...)`，保护：

- v1033 index 文件存在；
- index `status=pass`；
- index decision 是 v1033 ready；
- summary/body 都 ready；
- lookup scope 与 granted use 都是 downstream lookup only；
- lookup-ready 与 contract-check-ready 都为 true；
- receipt index row 数量为 1；
- lookup key 使用 v1033 namespace；
- source evidence 数量为 2；
- source evidence digest 非空；
- source evidence status 都是 pass；
- source receipt、source check、source review、source receipt index 路径仍存在；
- consumer boundary 与 model quality claim 保持 bounded；
- promotion 和 approval 都保持 false；
- v1033 next step 指向 v1034 review。

如果任何检查失败，review 不会 ready。

## CLI 流程

真实运行命令：

```text
python scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1034.py e/1033/解释/receipt-index-v1033 --out-dir e/1034/解释/receipt-index-review-v1034 --require-review-ready --require-lookup-ready --force
```

目录输入会自动定位：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1033.json
```

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1034_ready
review_ready=True
review_status=approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only
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
e/1034/图片/v1034-receipt-index-review.png
```

## 测试覆盖

focused 测试覆盖五条路径：

- ready v1033 index 可以通过 review；
- `granted_use` 改为 production promotion 会失败；
- source evidence digest 缺失会失败；
- source receipt path 漂移会失败；
- artifact writer 和 CLI 都能写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
5 passed in 11.63s
```

全量回归结果：

```text
2549 passed in 656.94s
```

source encoding hygiene 结果：

```text
source_count=1998
clean_count=1998
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1034 把 v1033 digest-backed index 审查为下一步 lookup-only receipt recording 的合格输入，但仍然明确阻断 production promotion。

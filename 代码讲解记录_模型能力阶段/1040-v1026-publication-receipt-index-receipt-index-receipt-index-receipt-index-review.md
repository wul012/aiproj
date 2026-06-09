# v1026 publication receipt index receipt index receipt index receipt index review 代码讲解

## 本版目标和边界

v1026 的目标是审查 v1025 digest-backed receipt index，确认它能进入下一步 lookup-only receipt recording。

它解决的问题是：v1025 已经把 receipt/check 合并成索引，但下游不应该直接信任这个索引。v1026 用独立 review 再检查一遍 index ready、lookup-only scope、source evidence digest、source path 和 no-promotion 边界。

本版不做模型训练，不修改评估结果，不开放生产晋级。

## 前置能力

v1025 生成了：

```text
e/1025/解释/receipt-index-v1025/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.json
```

该文件包含：

- 1 条 `receipt_index_rows`；
- 2 条 `source_evidence_rows`；
- receipt/check 输入路径；
- receipt/check 输入 SHA-256；
- `lookup_ready=True`；
- `contract_check_ready=True`；
- `promotion_ready=False`。

v1026 只审查这个索引，不重新生成 v1023 receipt 或 v1024 check。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.py`
  - v1026 review 核心模块。
  - 验证 v1025 index 是否仍然满足 lookup-only recording 的消费条件。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1026.py`
  - 命令行入口。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.py`
  - 覆盖 ready 路径、篡改失败路径、路径漂移失败路径和 CLI 输出。
- `e/1026/解释/receipt-index-review-v1026/`
  - 真实运行产物。
- `e/1026/图片/v1026-receipt-index-review.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`review` 是本版最核心的输出对象：

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
source_receipt_path
source_receipt_check_path
source_review_path
source_receipt_index_path
next_step
```

其中 `review_status` 固定为：

```text
approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only
```

它表示“允许进入 lookup-only receipt recording”，不是生产批准。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026(...)` 是主入口。

它读取 v1025 index 后，提取：

- `index_summary`
- `receipt_index`
- `receipt_index_rows`
- `source_evidence_rows`

然后调用 `_checks(...)`。

`_checks(...)` 保护以下条件：

- v1025 index 文件仍然存在；
- v1025 index 自身是 `status=pass`；
- decision 是 v1025 ready；
- summary/body 都显示 index ready；
- lookup scope 和 granted use 都是 downstream lookup only；
- lookup-ready 与 contract-check-ready 都为 true；
- receipt index row 数量仍然是 1；
- lookup key 使用 v1025 命名空间；
- source evidence 数量是 2；
- source evidence digest 非空；
- source evidence status 都是 pass；
- source receipt、source receipt check、source review、source receipt index 路径仍存在；
- model quality claim 仍然 bounded；
- promotion 仍然关闭；
- v1025 next step 指向 v1026 review。

只要任一检查失败，review 就不会进入 ready 状态。

## CLI 流程

真实运行命令：

```text
python scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1026.py e/1025/解释/receipt-index-v1025 --out-dir e/1026/解释/receipt-index-review-v1026 --require-review-ready --require-lookup-ready --force
```

CLI 支持传目录，locator 会自动找到：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_v1025.json
```

`--require-review-ready` 与 `--require-lookup-ready` 让脚本在 review 不通过时返回非零状态，适合后续 CI 或自动化消费。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026_ready
review_ready=True
review_status=approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only
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
e/1026/图片/v1026-receipt-index-review.png
```

## 测试覆盖

focused 测试覆盖五条路径：

- ready v1025 index 可以通过 review；
- `granted_use` 改成 `production_promotion` 会失败；
- source evidence digest 缺失会失败；
- source receipt path 漂移会失败；
- CLI 可以从目录定位输入并写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
5 passed in 8.48s
```

全量回归结果：

```text
2507 passed in 509.51s
```

source encoding hygiene 结果：

```text
source_count=1966
clean_count=1966
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1026 把 v1025 digest-backed index 推进为已审查的 lookup-only receipt recording 输入，但仍然没有把任何治理证据升级成模型生产能力。

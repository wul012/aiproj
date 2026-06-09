# v1027 publication receipt index receipt index receipt index receipt index receipt 代码讲解

## 本版目标和边界

v1027 的目标是记录 v1026 已审查 receipt index 的 downstream lookup-only receipt。

它解决的问题是：v1026 review 说明 v1025 index 可以被消费，但消费行为本身也需要留下可复核的 receipt。本版把消费方、消费用途、源 review digest、源 index row、源 evidence 和 no-promotion 边界固定下来。

本版不做模型训练，不改变 holdout 评估结果，不证明模型能力提升，也不开放 production promotion。

## 前置能力

v1026 生成了：

```text
e/1026/解释/receipt-index-review-v1026/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json
```

该文件包含：

- `review_ready=True`；
- `review_status=approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only`；
- 1 条 `receipt_index_rows`；
- 2 条 `source_evidence_rows`；
- `lookup_ready=True`；
- `contract_check_ready=True`；
- `promotion_ready=False`。

v1027 只消费这个 review，不重新生成 v1025 index，也不重新审查 v1023 receipt 或 v1024 check。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.py`
  - v1027 receipt 核心模块。
  - 验证 v1026 review 是否仍可被 downstream lookup reader 消费。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.py`
  - 命令行入口。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.py`
  - 覆盖 ready 路径、篡改失败路径、路径漂移失败路径和 CLI 输出。
- `e/1027/解释/receipt-v1027/`
  - 真实运行产物。
- `e/1027/图片/v1027-receipt.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`receipt` 是本版核心输出对象：

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

其中 `receipt_status` 固定为：

```text
publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted
```

它表示“下游 lookup reader 的只读消费已登记”，不是生产发布批准。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027(...)` 是主入口。

它读取 v1026 review 后，提取：

- `summary`
- `review`
- `receipt_index_rows`
- `source_evidence_rows`

然后调用 `_checks(...)`。

`_checks(...)` 保护以下条件：

- v1026 review 文件仍然存在；
- v1026 review 自身是 `status=pass`；
- decision 是 v1026 ready；
- summary/body 都显示 review ready；
- review status 只允许 lookup-only recording；
- requested use 必须是 downstream governance lookup only；
- source granted use 仍然是 downstream lookup only；
- receipt index lookup 与 contract check 都是 ready；
- index row 数量仍然是 1；
- source evidence 数量仍然是 2；
- source evidence digest 非空；
- source evidence status 都是 pass；
- lookup key 使用 v1025 source namespace；
- index row 没有 promotion；
- summary/body 的 promotion flags 都是 false；
- consumer boundary 仍然是治理查阅边界；
- model quality claim 仍然是 bounded；
- source receipt index、source receipt、source receipt check、source review、source origin index 路径仍存在；
- source failed check count 仍然是 0；
- source next step 指向本版 receipt。

只要任一检查失败，本版 receipt 就不会 ready。

## CLI 流程

真实运行命令：

```text
python scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027.py e/1026/解释/receipt-index-review-v1026 --out-dir e/1027/解释/receipt-v1027 --require-receipt-ready --force
```

CLI 支持传目录，locator 会自动找到：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_review_v1026.json
```

`--require-receipt-ready` 让脚本在 receipt 不通过时返回非零状态，适合后续 CI 或自动化消费。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_ready
receipt_ready=True
receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_receipted
consumer_name=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1027_lookup_reader
granted_use=downstream_governance_lookup_only
receipt_index_row_count=1
source_evidence_count=2
lookup_key_count=1
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

HTML 报告截图保存到：

```text
e/1027/图片/v1027-receipt.png
```

## 测试覆盖

focused 测试覆盖六条路径：

- ready v1026 review 可以登记 receipt；
- `requested_use` 改成 `production_promotion` 会失败；
- source review path 漂移会失败；
- source evidence status 被改坏会失败；
- `--require-receipt-ready` 对失败输入返回非零；
- CLI 可以从目录定位输入并写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
6 passed in 8.21s
```

全量回归结果：

```text
2513 passed in 444.16s
```

source encoding hygiene 结果：

```text
source_count=1970
clean_count=1970
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1027 把 v1026 review 变成可追溯的 downstream lookup-only receipt，但仍然没有把治理消费链条升级成生产模型能力。

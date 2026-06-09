# v1035 publication receipt index receipt index receipt index receipt index receipt index receipt index receipt 代码讲解

## 本版目标和边界

v1035 的目标是把 v1034 已审查通过的 digest-backed receipt index 记录为 downstream lookup-only receipt。

它解决的问题是：v1034 review 说明 v1033 index 可以进入下一步，但下游治理消费仍需要一份明确的 receipt，写清谁在消费、消费用途是什么、它引用的上游 review 和 source evidence 是否仍然存在。v1035 就是这层 receipt。

本版不做模型训练，不改变模型评分，不批准生产推广。它只记录 lookup-only 使用权。

## 前置能力

v1034 输出：

```text
e/1034/解释/receipt-index-review-v1034/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1034.json
```

这份 review 已确认：

- `review_ready=True`；
- `review_status=approved_for_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_lookup_only`；
- `lookup_ready=True`；
- `contract_check_ready=True`；
- `source_evidence_count=2`；
- `promotion_ready=False`。

v1035 只消费这份 review，不重建 v1033 index，也不重新评价模型能力。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035.py`
  - v1035 receipt 核心模块。
  - 检查 v1034 review 是否仍满足 downstream lookup-only receipt 条件。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035.py`
  - CLI 入口。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035.py`
  - 覆盖 ready、requested use 漂移、source path 漂移、source evidence status 漂移、CLI require 失败和 artifact 输出。
- `e/1035/解释/receipt-v1035/`
  - 真实运行产物。
- `e/1035/图片/v1035-receipt.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`receipt` 是本版的核心输出：

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

`receipt_status` 固定为：

```text
publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035_lookup_receipted
```

这表示“已记录 lookup-only receipt”，不是模型上线批准。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035(...)` 是主入口。

它读取 v1034 review 后，拆出：

- `summary`
- `review`
- `receipt_index_rows`
- `source_evidence_rows`

然后 `_checks(...)` 保护以下边界：

- v1034 review 文件存在；
- review `status=pass`；
- review decision 是 v1034 ready；
- summary 和 body 都 ready；
- review status 只允许 lookup-only receipt recording；
- requested use 必须是 downstream governance lookup only；
- granted use 必须保持 downstream lookup only；
- lookup-ready 与 contract-check-ready 都为 true；
- receipt index row 数量为 1；
- source evidence 数量为 2；
- source evidence digest 非空；
- source evidence status 都是 pass；
- lookup key 使用 v1033 source namespace；
- index row 没有被 promoted；
- promotion 和 approved_for_promotion 都是 false；
- consumer boundary 与 model quality claim 保持治理查询和 bounded claim；
- source receipt index、receipt、contract check、review、origin index 路径仍存在；
- v1034 review 的 next step 指向 receipt recording。

任意检查失败时，receipt 不 ready，`--require-receipt-ready` 会返回非 0。

## CLI 流程

真实运行命令：

```text
python scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035.py e/1034/解释/receipt-index-review-v1034 --out-dir e/1035/解释/receipt-v1035 --require-receipt-ready --force
```

目录输入会自动定位：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1034.json
```

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035_ready
receipt_ready=True
receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035_lookup_receipted
consumer_name=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1035_lookup_reader
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
e/1035/图片/v1035-receipt.png
```

## 测试覆盖

focused 测试覆盖六条路径：

- ready v1034 review 可以生成 receipt；
- requested use 改成 production promotion 会失败；
- source review path 漂移会失败；
- source evidence status 改成 fail 会失败；
- `--require-receipt-ready` 对坏 review 返回 `1`；
- artifact writer 和 CLI 都能写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
6 passed in 10.75s
```

全量回归结果：

```text
2555 passed in 472.54s
```

source encoding hygiene 结果：

```text
source_count=2002
clean_count=2002
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1035 把 v1034-reviewed receipt index 记录成下游治理可查询 receipt，但仍把 production promotion 明确挡在链路之外。

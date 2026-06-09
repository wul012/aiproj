# v1031 publication receipt index receipt index receipt index receipt index receipt index receipt 代码讲解

## 本版目标和边界

v1031 的目标是把 v1030 已审查通过的 digest-backed receipt index 记录成 downstream lookup-only receipt。

它解决的问题是：v1030 只是确认 v1029 index 可以进入 receipt recording，但下游还需要一个独立 receipt 产物来声明“谁可以用、只能怎么用、源证据来自哪里、下一步要做什么”。v1031 就是这层 receipt。

本版不做模型训练，不改变评估分数，不开放生产推广，也不把治理 evidence 解释成模型质量提升。

## 前置能力

v1030 输出了：

```text
e/1030/解释/receipt-index-review-v1030/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1030.json
```

该 review 已确认：

- v1029 index ready；
- lookup scope 是 downstream governance lookup only；
- source evidence 有 2 条且 digest/status 干净；
- v1027 receipt、v1028 check、v1030 review 相关源路径存在；
- `promotion_ready=False`；
- 下一步应进入 v1031 receipt recording。

v1031 只消费这个 review，不重建 v1027 receipt，也不重新跑 v1028 contract check。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031.py`
  - v1031 receipt 核心模块。
  - 校验 v1030 review 是否仍满足 receipt recording 条件。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_artifacts.py`
  - 写出 JSON、CSV、Text、Markdown、HTML。
- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031.py`
  - 命令行入口，支持传入 review JSON 或 review 输出目录。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031.py`
  - 覆盖 ready 路径、requested use 漂移、source path 漂移、source evidence status 变坏、CLI fail-fast 和 artifact 输出。
- `e/1031/解释/receipt-v1031/`
  - 真实运行产物。
- `e/1031/图片/v1031-receipt.png`
  - Playwright MCP 截图证据。

## 核心数据结构

`receipt` 是本版的核心输出对象：

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
publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_lookup_receipted
```

这表示 receipt 已记录为 lookup-only consumption，不代表模型可发布。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031(...)` 是主入口。

它读取 v1030 review 后拆出：

- `review_summary`
- `review`
- `receipt_index_rows`
- `source_evidence_rows`

然后调用 `_checks(...)`。这些检查保护：

- v1030 review 文件仍存在；
- review 自身 `status=pass`；
- review decision 是 v1030 ready；
- summary/body 都显示 review ready；
- review status 允许进入 lookup-only receipt recording；
- requested use 必须是 `downstream_governance_lookup_only`；
- granted use 必须保持 lookup-only；
- receipt index 与 lookup 都 ready；
- contract check 已 ready；
- receipt index row 数量是 1；
- source evidence 数量是 2；
- source evidence digest 非空；
- source evidence status 都是 pass；
- lookup key 仍属于 v1029 source namespace；
- index rows 与 review 都没有 promotion；
- consumer boundary 与 model quality claim 保持 bounded；
- source receipt、source check、source review、source origin index 路径仍存在；
- v1030 next step 指向 v1031 receipt。

如果任何检查失败，输出仍会写出报告，但 `receipt_ready=False`，`--require-receipt-ready` 会让 CLI 返回非零状态。

## CLI 流程

真实运行命令：

```text
python scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031.py e/1030/解释/receipt-index-review-v1030 --out-dir e/1031/解释/receipt-v1031 --require-receipt-ready --force
```

CLI 支持目录输入，locator 会自动找到：

```text
randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1030.json
```

输出包括：

- JSON：供后续 contract check 读取；
- CSV：记录 consumer receipt 行；
- Text：适合命令行快速确认；
- Markdown：适合归档阅读；
- HTML：适合截图和人工检查。

## 运行证据

真实 CLI 输出关键值：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_ready
receipt_ready=True
receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_lookup_receipted
consumer_name=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1031_lookup_reader
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
e/1031/图片/v1031-receipt.png
```

## 测试覆盖

focused 测试覆盖六条路径：

- ready v1030 review 可以生成 lookup-only receipt；
- requested use 改成 `production_promotion` 会失败；
- source review path 漂移会失败；
- source evidence status 变成 fail 会失败；
- CLI 在坏 review + `--require-receipt-ready` 下返回 1；
- artifact writer 和 CLI 都能写出 JSON、CSV、Text、Markdown、HTML。

当前 focused 测试结果：

```text
6 passed in 7.48s
```

全量回归结果：

```text
2534 passed in 408.50s
```

source encoding hygiene 结果：

```text
source_count=1986
clean_count=1986
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 一句话总结

v1031 把 v1030 审查通过的 receipt index 变成下游可查询的 lookup-only receipt，但仍然明确阻断模型生产晋级。

# v1023：publication receipt index receipt index receipt index receipt

## 本版目标和边界

v1023 的目标是把 v1022 review 记录成 downstream lookup-only receipt。它让后续 contract check 可以围绕一个稳定 receipt 做重建验证，而不是直接消费 v1022 的 review artifact。

本版不做模型训练，不改变 checkpoint，不提升模型质量结论，也不允许 production promotion。它只是在治理链里确认：v1022 审查通过的 receipt index 可以被一个明确 consumer 以 lookup-only 方式消费。

## 前置能力

v1021 生成 digest-backed receipt index，v1022 对该 index 做 review。v1023 消费 v1022 的结果，并重点确认：

- `review_ready=True`
- `review_status=approved_for_publication_receipt_index_receipt_index_receipt_index_lookup_only`
- `lookup_ready=True`
- `contract_check_ready=True`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023.py`
  - 核心 receipt builder。
  - 校验 v1022 review、lookup-only use、source evidence、source paths、bounded claim、no-promotion 和 next-step。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - HTML 参与 Playwright MCP 截图。

- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023.py`
  - CLI 入口，接收 v1022 review JSON 或输出目录。
  - 支持 consumer name、requested use、require receipt ready、require promotion ready 和 force。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023.py`
  - 覆盖 ready 输入、requested use 篡改、source path 漂移、source evidence status 漂移、CLI require 失败和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1023_NEXT_STEP`。

## 核心数据结构

`receipt` 是本版的主要输出对象，包含：

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
- `consumer_boundary`
- `model_quality_claim`
- `source_receipt_index_path`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_origin_path`
- `next_step`

`consumer_receipts` 是给下游读取的表格视图。每一行把 consumer、lookup key、receipt index id、source receipt id、当前 receipt id、granted use、promotion flag 和 receipt status 放在一起。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023(...)` 读取 v1022 review report，拆出 `summary`、`review`、`receipt_index_rows` 和 `source_evidence_rows`，再执行 `_checks(...)`。

`_checks(...)` 验证：

- v1022 review JSON 文件仍存在；
- v1022 review 自身 `status=pass`；
- decision 是 `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022_ready`；
- summary 和 body 都 review ready；
- review status 是 lookup-only receipt recording；
- requested use 只能是 downstream governance lookup only；
- granted use 仍是 lookup-only；
- receipt index lookup ready，contract check ready；
- index row count 为 1；
- source evidence count 为 2，digest 存在，status 为 pass；
- lookup key 使用 v1021 namespace；
- index rows 没有 promotion；
- consumer boundary 和 model quality claim 没有扩大；
- v1021 index、v1019 receipt、v1020 check、v1018 review、v1017 source index 仍存在；
- v1022 review checks clean；
- v1022 next step 等于常量 `record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1022`。

`_receipt(...)` 只在所有检查通过时生成 receipt，并把下一步路由到：

```text
check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023
```

## 输出产物

真实运行输出写入：

```text
e/1023/解释/receipt-v1023/
```

截图写入：

```text
e/1023/图片/v1023-receipt.png
```

这些产物是 lookup-only receipt 证据，不是模型训练结果，也不是上线凭证。

## 测试覆盖

focused 测试覆盖：

- ready v1022 review 能生成 receipt；
- requested use 改成 `production_promotion` 时失败；
- source review path 漂移时失败；
- source evidence status 改成 fail 时失败；
- `--require-receipt-ready` 在坏 review 下返回 1；
- CLI、locator 和五类 artifact 输出全部连通。

当前 focused 测试结果：

```text
6 passed in 8.58s
```

全量回归结果：

```text
2492 passed in 424.79s
```

source encoding hygiene 结果：

```text
status=pass
source_count=1954
clean_count=1954
syntax_error_count=0
```

## 运行证据

真实 CLI 关键结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023_ready
receipt_ready=True
receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_v1023_lookup_receipted
granted_use=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

## 一句话总结

v1023 把 v1022 review 记录成可复核、可重建、仍然 lookup-only 的 downstream receipt，为下一步 contract check 准备了稳定输入。

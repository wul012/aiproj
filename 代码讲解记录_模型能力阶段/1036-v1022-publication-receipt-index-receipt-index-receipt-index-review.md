# v1022：publication receipt index receipt index receipt index review

## 本版目标和边界

v1022 的目标是审查 v1021 生成的 digest-backed receipt index，确认它可以作为下一步 lookup-only receipt 的来源。

本版不做模型训练，不改变 checkpoint，不提升模型质量结论，也不允许 production promotion。它只回答一个工程问题：v1021 的 index 是否仍然可读、可查、可复核，并且没有把治理 lookup-only 证据扩大成生产发布依据。

## 前置能力

v1019 记录 lookup-only receipt，v1020 对该 receipt 做 contract check，v1021 把两者合并成 digest-backed receipt index。v1022 消费 v1021 的结果，并重点确认：

- `index_ready=True`
- `lookup_ready=True`
- `contract_check_ready=True`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022.py`
  - 核心 review builder。
  - 校验 v1021 index 的 ready 状态、lookup-only 边界、source evidence、source paths、bounded claim、no-promotion 和 next-step。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - HTML 参与 Playwright MCP 截图，是运行证据的一部分。

- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1022.py`
  - CLI 入口，接收 v1021 receipt index JSON 或输出目录。
  - 支持 `--require-review-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022.py`
  - 覆盖 ready 输入、granted use 篡改、source evidence digest 缺失、source path 漂移、CLI 和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1022_NEXT_STEP`。

## 核心数据结构

`review` 是本版的主要输出对象，包含：

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
- `granted_use`
- `promotion_ready`
- `approved_for_promotion`
- `consumer_boundary`
- `model_quality_claim`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_path`
- `next_step`

这些字段让后续 receipt 版本不需要重新理解整个 v1017-v1021 链路，只需要读取 v1022 review 结果即可判断能否继续。

`check_rows` 是审计面，每个 row 包含：

- `id`
- `status`
- `actual`
- `detail`

失败检查会进入 `issues`，同时 `receipt_index_rows` 和 `source_evidence_rows` 不再向外透出，避免坏 index 被下游误用。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022(...)` 读取 v1021 index report，拆出 `summary`、`receipt_index`、`receipt_index_rows` 和 `source_evidence_rows`，然后执行 `_checks(...)`。

`_checks(...)` 验证：

- v1021 index JSON 文件仍存在；
- v1021 index 自身 `status=pass`；
- decision 是 `randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021_ready`；
- summary 和 body 都 ready；
- lookup scope 和 granted use 都是 `downstream_governance_lookup_only`；
- lookup key namespace 来自 v1021 的 `LOOKUP_KEY_PREFIX`；
- source evidence count 为 2；
- source evidence digest 存在且状态为 pass；
- v1019 receipt、v1020 check、v1018 review、v1017 source index 路径仍存在；
- consumer boundary 和 model quality claim 没有扩大；
- promotion 仍为 false；
- v1021 source checks 为 clean；
- v1021 next step 等于常量 `review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021`。

`_review(...)` 只在所有检查通过时生成 review-ready 对象，并把下一步路由到：

```text
record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1022
```

## 输出产物

真实运行输出写入：

```text
e/1022/解释/receipt-index-review-v1022/
```

截图写入：

```text
e/1022/图片/v1022-receipt-index-review.png
```

这些产物是 lookup-only review 证据，不是模型训练结果，也不是上线凭证。

## 测试覆盖

focused 测试覆盖：

- ready v1021 index 能生成 review；
- `granted_use` 改成 `production_promotion` 时失败；
- source evidence digest 为空时失败；
- source receipt path 漂移时失败；
- CLI、locator 和五类 artifact 输出全部连通。

当前 focused 测试结果：

```text
5 passed in 9.81s
```

全量回归结果：

```text
2486 passed in 511.28s
```

source encoding hygiene 结果：

```text
status=pass
source_count=1950
clean_count=1950
syntax_error_count=0
```

## 运行证据

真实 CLI 关键结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_review_v1022_ready
review_ready=True
review_status=approved_for_publication_receipt_index_receipt_index_receipt_index_lookup_only
lookup_key_count=1
source_evidence_count=2
contract_check_ready=True
promotion_ready=False
passed_check_count=22
failed_check_count=0
```

## 一句话总结

v1022 把 v1021 的 digest-backed receipt index 变成可审查、可传递、仍然 lookup-only 的 review 证据，为下一步记录 receipt 提供受控入口。

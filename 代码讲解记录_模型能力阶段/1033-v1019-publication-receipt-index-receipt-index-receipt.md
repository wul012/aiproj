# v1019：publication receipt index receipt index receipt

## 本版目标和边界

v1019 的目标是把 v1018 审查通过的 receipt index 记录为 downstream lookup-only receipt。这样后续 contract check 可以复核 receipt 是否能从 v1018 review 重新推导出来。

本版不训练模型，不改变 checkpoint，不宣称 baseline/candidate 有新提升，也不打开 production promotion。它只把上一版 review 的结果登记成一份可追溯的 receipt。

## 前置能力

v1018 已经审查了 v1017 short-name receipt index，确认：

- `review_ready=True`
- `lookup_ready=True`
- `contract_check_ready=True`
- `receipt_index_row_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `failed_check_count=0`

v1019 消费这份 review，并把它转化为下一步 contract check 的输入。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019.py`
  - 核心 receipt builder。
  - 校验 v1018 review 的状态、用途、source evidence、source paths、bounded claim 和 no-promotion。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - CSV 保存 consumer receipt rows，HTML 用于截图。

- `scripts/record_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019.py`
  - CLI 入口。
  - 支持 `--require-receipt-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019.py`
  - 覆盖 ready review、requested use 篡改、source path 漂移、source evidence status 篡改、CLI 和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_V1019_NEXT_STEP`。

## 核心数据结构

`receipt` 是本版的主要输出对象。它包含：

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

`consumer_receipts` 是给下游使用的行式视图。每一行记录 consumer、lookup key、source receipt id、本版 receipt id、granted use、promotion 状态和 receipt status。

## 核心函数

`locate_receipt_index_review_v1019(...)` 支持传入 v1018 review JSON 或输出目录。如果传入目录，它会自动定位 v1018 的 JSON 文件名。

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019(...)` 是主函数：

1. 读取 v1018 review 的 `summary`、`review`、`receipt_index_rows` 和 `source_evidence_rows`。
2. 调用 `_checks(...)` 生成检查列表。
3. 如果检查全部通过，调用 `_receipt(...)` 生成 receipt。
4. 生成 `consumer_receipts`、`summary` 和 `interpretation`。

`_checks(...)` 保护的关键边界包括：

- v1018 review 文件存在；
- v1018 report 为 `status=pass`；
- v1018 decision 和 ready key 都正确；
- review status 只允许 lookup-only receipt recording；
- requested use 必须是 downstream governance lookup only；
- granted use 必须仍是 downstream lookup only；
- receipt index lookup 和 contract check 都 ready；
- receipt index row 只有 1 条；
- source evidence 为 2 条，且每条都有 SHA-256、状态为 pass；
- lookup key 必须使用 v1017 source namespace；
- index row 没有 promotion；
- summary/review 的 promotion 和 approved 标记都保持 False；
- consumer boundary 和 model quality claim 没有扩大；
- v1018/v1017/v1016/v1015/v1014/v1013 源路径仍存在；
- source failed check count 为 0；
- v1018 next step 指向 v1019 receipt recording。

`resolve_exit_code(...)` 让 CLI 可以作为 gate 使用：

- `--require-receipt-ready`：receipt 不 ready 返回 1；
- `--require-promotion-ready`：promotion 不 ready 返回 1。

当前真实 v1019 证据不允许 promotion，因此 `--require-promotion-ready` 返回 1 是预期行为。

## 输出产物

真实运行输出写入：

```text
e/1019/解释/receipt-v1019/
```

截图写入：

```text
e/1019/图片/v1019-receipt.png
```

JSON 是后续 contract check 的输入。CSV 是 consumer receipt 行式视图。Text 用于 CLI 摘要。Markdown 和 HTML 用于人工审查与截图证据。

## 测试覆盖

focused 测试覆盖：

- ready v1018 review 能生成 receipt；
- `requested_use` 改成 `production_promotion` 时失败；
- source review path 漂移时失败；
- source evidence status 被改成 fail 时失败；
- CLI、locator 和五类 artifact 输出都连通。

当前 focused 结果：

```text
11 passed in 24.12s
```

全量回归结果：

```text
2471 passed in 529.93s
```

source encoding hygiene 结果：

```text
status=pass
source_count=1938
clean_count=1938
syntax_error_count=0
```

## 运行证据

真实 CLI 关键结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019_ready
receipt_ready=True
receipt_status=publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted
consumer_name=publication_receipt_index_receipt_index_receipt_v1019_lookup_reader
granted_use=downstream_governance_lookup_only
lookup_key_count=1
source_evidence_count=2
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

Playwright MCP 截图确认 HTML 页面可见 `Status=pass`、`Receipt ready=True`、`Failed=0`，以及从 v1019 回溯到 v1013 的源路径。

## 一句话总结

v1019 把 v1018 review 登记成下一步可复核的 lookup-only receipt，让短名链路继续推进，同时不扩大模型质量和 promotion 边界。

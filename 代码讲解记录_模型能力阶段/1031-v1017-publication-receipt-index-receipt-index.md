# v1017：publication receipt index receipt index

## 本版目标和边界

v1017 的目标是把 v1015 short-name receipt 和 v1016 contract check 合并成一个 digest-backed receipt index。这样后续 review 不需要分别读取两份产物，而是可以通过一个 index 同时看到 lookup row、source evidence 和 no-promotion 边界。

本版不做模型能力提升，不改变训练结果，也不允许 production promotion。它只是把已验证的 lookup-only receipt 证据整理成可索引形态。

## 前置能力

v1015 记录了 lookup-only receipt，v1016 证明该 receipt 可以从 v1014 source review 重建。v1017 消费这两个结果：

- `receipt_ready=True`
- `contract_check_ready=True`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_v1017.py`
  - 核心 index builder。
  - 校验 receipt、contract check、source paths、bounded claim、lookup-only use 和 no-promotion。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_v1017_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - HTML 用于 Playwright MCP 截图。

- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_v1017.py`
  - CLI 入口，接收 `--receipt` 和 `--receipt-check`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_v1017.py`
  - 覆盖 ready 输入、granted use 篡改、contract check not ready、CLI 和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_V1017_NEXT_STEP`。

## 核心数据结构

`receipt_index_rows` 是本版的主要消费面。它包含：

- `receipt_index_id`
- `lookup_key`
- `receipt_id`
- `receipt_status`
- `granted_use`
- `source_receipt_path`
- `source_receipt_check_path`
- `source_review_path`
- `source_receipt_index_path`
- `contract_check_ready`
- `promotion_ready`

`source_evidence_rows` 保存两条 digest 证据：

- v1015 receipt JSON
- v1016 receipt check JSON

每条 source evidence 都包含 `kind`、`path`、`sha256` 和 `status`。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_v1017(...)` 读取 receipt 和 check，执行 `_checks(...)`，再调用 `_index(...)` 构建 index。

`_checks(...)` 验证：

- receipt/check 文件存在；
- receipt status 为 pass，decision 为 v1015 ready；
- receipt summary 和 body 都 ready；
- v1016 contract check 为 pass；
- original/rebuilt receipt status 与 receipt status 一致；
- granted use 仍是 downstream governance lookup only；
- lookup key count 为 1；
- v1015 声明的 source review、source receipt index、source receipt 和 source receipt check 仍存在；
- consumer boundary 和 model quality claim 没有扩大；
- promotion 仍然关闭；
- source receipt 和 source contract check 的 failed count 都是 0；
- receipt/check 的 next step 符合 v1015/v1016 常量。

`_index(...)` 只在 checks 全部通过时生成 index row，并写入 `source_evidence_rows`。如果任何一项失败，index row 会保持空，避免下游误消费坏证据。

## 测试覆盖

focused 测试覆盖四类场景：

- ready receipt/check 能生成 index。
- `granted_use` 改成 `production_promotion` 时失败。
- contract check not ready 时失败。
- CLI、locator 和五类 artifact 输出全部连通。

全量回归结果为：

```text
2460 passed in 477.69s
```

## 运行证据

真实 CLI 运行写入：

- `e/1017/解释/receipt-index-v1017/randomized_holdout_publication_receipt_index_receipt_index_v1017.json`
- `e/1017/解释/receipt-index-v1017/randomized_holdout_publication_receipt_index_receipt_index_v1017.html`

关键结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_v1017_ready
index_ready=True
lookup_key_count=1
source_evidence_count=2
contract_check_ready=True
promotion_ready=False
failed_check_count=0
```

截图归档在：

```text
e/1017/图片/v1017-receipt-index.png
```

## 一句话总结

v1017 把 v1015 receipt 和 v1016 contract check 收束成一个短名、可查找、带 digest 的 lookup-only receipt index。

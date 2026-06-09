# v1021：publication receipt index receipt index receipt index

## 本版目标和边界

v1021 的目标是把 v1019 lookup-only receipt 和 v1020 contract check 合并为 digest-backed receipt index。

本版不做模型训练，不改变 checkpoint，不提升模型质量结论，也不允许 production promotion。它只是把已验证的 receipt 证据整理成可索引形态。

## 前置能力

v1019 记录了 lookup-only receipt，v1020 证明该 receipt 可以从 v1018 source review 重建。v1021 消费这两个结果：

- `receipt_ready=True`
- `contract_check_ready=True`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021.py`
  - 核心 index builder。
  - 校验 receipt、contract check、source paths、bounded claim、lookup-only use 和 no-promotion。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - HTML 用于 Playwright MCP 截图。

- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021.py`
  - CLI 入口，接收 `--receipt` 和 `--receipt-check`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021.py`
  - 覆盖 ready 输入、granted use 篡改、contract check not ready、CLI 和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_V1021_NEXT_STEP`。

## 核心数据结构

`receipt_index_rows` 是本版的主要消费面，包含：

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

- v1019 receipt JSON
- v1020 receipt check JSON

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021(...)` 读取 receipt 和 check，执行 `_checks(...)`，再调用 `_index(...)` 构建 index。

`_checks(...)` 验证：

- receipt/check 文件存在；
- receipt status 为 pass，decision 为 v1019 ready；
- receipt summary 和 body 都 ready；
- v1020 contract check 为 pass；
- original/rebuilt receipt status 与 receipt status 一致；
- granted use 仍是 downstream governance lookup only；
- lookup key count 为 1；
- v1019 声明的 source review、source receipt index、source receipt 和 source receipt check 仍存在；
- consumer boundary 和 model quality claim 没有扩大；
- promotion 仍然关闭；
- source receipt 和 source contract check 的 failed count 都是 0；
- receipt/check 的 next step 符合 v1019/v1020 常量。

`_index(...)` 只在 checks 全部通过时生成 index row，并写入 `source_evidence_rows`。任何失败都会让 index row 保持空，避免下游误消费坏证据。

## 输出产物

真实运行输出写入：

```text
e/1021/解释/receipt-index-v1021/
```

截图写入：

```text
e/1021/图片/v1021-receipt-index.png
```

## 测试覆盖

focused 测试覆盖：

- ready receipt/check 能生成 index；
- `granted_use` 改成 `production_promotion` 时失败；
- contract check not ready 时失败；
- CLI、locator 和五类 artifact 输出全部连通。

当前 focused 测试结果：

```text
10 passed in 14.31s
```

全量回归结果：

```text
2481 passed in 471.76s
```

source encoding hygiene 结果：

```text
status=pass
source_count=1946
clean_count=1946
syntax_error_count=0
```

## 运行证据

真实 CLI 关键结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_v1021_ready
index_ready=True
lookup_key_count=1
source_evidence_count=2
contract_check_ready=True
promotion_ready=False
passed_check_count=25
failed_check_count=0
```

## 一句话总结

v1021 把 v1019 receipt 和 v1020 contract check 收束成一个短名、可查找、带 digest 的 lookup-only receipt index。

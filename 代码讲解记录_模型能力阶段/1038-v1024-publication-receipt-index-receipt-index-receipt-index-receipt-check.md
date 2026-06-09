# v1024：publication receipt index receipt index receipt index receipt check

## 本版目标和边界

v1024 的目标是对 v1023 lookup-only receipt 做 contract check。它从 v1023 receipt 中找到 source review，再调用 v1023 builder 重新生成 receipt，最后比较稳定字段。

本版不做模型训练，不改变 checkpoint，不提升模型质量结论，也不允许 production promotion。它只证明：v1023 receipt 不是孤立 artifact，而是可以从 v1022 review 重新推导出来。

## 前置能力

v1022 审查 v1021 digest-backed receipt index，v1023 把该 review 记录成 lookup-only receipt。v1024 消费 v1023 receipt，并重点确认：

- 原始 receipt 和重建 receipt 的 `status` 一致；
- 原始 receipt 和重建 receipt 的 `decision` 一致；
- source review digest 一致；
- consumer receipts 一致；
- stable summary fields 一致；
- stable receipt fields 一致；
- original/rebuilt promotion 均为 false。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_check_v1024.py`
  - 核心 contract check builder。
  - 负责定位 source review、重建 v1023 receipt、比较稳定字段。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_check_v1024_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - HTML 用于 Playwright MCP 截图。

- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1024.py`
  - CLI 入口，接收 v1023 receipt JSON 或输出目录。
  - 支持 `--require-pass` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_check_v1024.py`
  - 覆盖可重建成功、granted use 篡改、source review 缺失、source digest 篡改、CLI require-pass 和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1024_NEXT_STEP`。

## 核心数据结构

`SUMMARY_FIELDS` 列出需要稳定重建的 summary 字段，包括：

- v1023 ready key；
- receipt id/type/status；
- consumer name；
- granted use；
- receipt index row count；
- source evidence count；
- lookup key count；
- promotion flags；
- consumer boundary；
- model quality claim；
- next step；
- passed/failed check count。

`RECEIPT_FIELDS` 列出 receipt body 里的稳定字段，包括：

- source review path 和 digest；
- lookup keys；
- review id/status；
- source receipt index、source receipt、source check、source review、origin index；
- no-promotion flags；
- next step。

`check_rows` 是本版的主要审计面，每条检查都包含 `id/status/actual/detail`。如果任何字段不一致，`status` 会变成 fail，`issues` 会保存失败行。

## 核心函数

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_check_v1024(...)` 接收 v1023 receipt report，拆出 original summary 和 original receipt，再调用 `_resolve_source_review_path(...)` 找到 v1022 review。

`_rebuild_receipt(...)` 读取 v1022 review，并调用：

```text
build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1023(...)
```

生成 rebuilt receipt。

`_checks(...)` 验证：

- source review 文件存在；
- original/rebuilt status 一致；
- original/rebuilt decision 一致；
- failed count 一致；
- source review sha256 一致；
- consumer receipts 一致；
- `SUMMARY_FIELDS` 中每个字段一致；
- `RECEIPT_FIELDS` 中每个字段一致。

`_summary(...)` 将 original/rebuilt 的关键对比结果提取给报告首页，并在通过时把 next step 指向：

```text
index_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_v1024
```

## 输出产物

真实运行输出写入：

```text
e/1024/解释/receipt-check-v1024/
```

截图写入：

```text
e/1024/图片/v1024-receipt-check.png
```

这些产物是 receipt contract check 证据，不是模型训练结果，也不是上线凭证。

## 测试覆盖

focused 测试覆盖：

- ready v1023 receipt 可以从 v1022 review 重建；
- summary/body 的 granted use 被改成 `production_promotion` 时失败；
- source review path 缺失时失败；
- source review digest 被改坏时失败；
- `--require-pass` 在坏 receipt 下返回 1；
- CLI、locator 和五类 artifact 输出全部连通。

当前 focused 测试结果：

```text
6 passed in 8.72s
```

全量回归结果：

```text
2498 passed in 494.32s
```

source encoding hygiene 结果：

```text
source_count=1958
clean_count=1958
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

## 运行证据

真实 CLI 关键结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_contract_check_v1024_passed
contract_check_ready=True
original_receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_v1023_lookup_receipted
rebuilt_receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_v1023_lookup_receipted
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_lookup_key_count=1
rebuilt_lookup_key_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

## 一句话总结

v1024 把 v1023 receipt 从“已记录”推进到“可重建验证”，为下一步 receipt index 提供可靠输入。

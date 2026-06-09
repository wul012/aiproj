# v1020：publication receipt index receipt index receipt check

## 本版目标和边界

v1020 的目标是对 v1019 lookup-only receipt 做 contract check。它读取 v1019 receipt 中记录的 v1018 source review，重新调用 v1019 receipt builder，然后比较原始 receipt 和重建 receipt 的稳定字段。

本版不做训练，不修改 checkpoint，不宣称模型能力提高，也不允许 production promotion。它只验证 receipt artifact 能否从源 review 复现。

## 前置能力

v1019 已经把 v1018 review 记录成 downstream lookup-only receipt。v1020 消费 v1019 的真实 JSON：

```text
e/1019/解释/receipt-v1019/randomized_holdout_publication_receipt_index_receipt_index_receipt_v1019.json
```

并回读其中的 source review：

```text
e/1018/解释/receipt-index-review-v1018/randomized_holdout_publication_receipt_index_receipt_index_review_v1018.json
```

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_check_v1020.py`
  - 核心 contract check builder。
  - 从 source review 重建 v1019 receipt，并比较稳定字段。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_check_v1020_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - CSV 保存 check rows，HTML 用于截图。

- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_v1020.py`
  - CLI 入口。
  - 支持 `--require-pass` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_check_v1020.py`
  - 覆盖成功重建、granted use 篡改、source review 缺失、digest 篡改、CLI 和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_RECEIPT_CHECK_V1020_NEXT_STEP`。

## 核心数据结构

`SUMMARY_FIELDS` 定义需要精确重建的 summary 字段，包括：

- ready key；
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

`RECEIPT_FIELDS` 定义 receipt body 的稳定字段，包括：

- receipt ready/id/type/status；
- requested/granted use；
- source review path 和 SHA-256；
- lookup keys；
- review id/status；
- no-promotion flags；
- bounded claim；
- v1018/v1017/v1016/v1015/v1014/v1013 相关 source path；
- next step。

`check_rows` 是最终审计输出。它既包含整体字段，例如 `status`、`decision`、`failed_count`、`consumer_receipts`，也包含 summary 和 receipt 的逐字段比对结果。

## 核心函数

`locate_receipt_v1020(...)` 支持传入 v1019 receipt JSON 或输出目录。如果传入目录，它会自动定位 v1019 JSON 文件名。

`build_randomized_holdout_publication_receipt_index_receipt_index_receipt_check_v1020(...)` 是主函数：

1. 读取 original summary 和 original receipt。
2. 调用 `_resolve_source_review_path(...)` 找到 v1018 source review。
3. 调用 `_rebuild_receipt(...)` 用 v1018 review 重新构建 v1019 receipt。
4. 调用 `_checks(...)` 比较 original 和 rebuilt。
5. 输出 contract summary、check rows 和 interpretation。

`_checks(...)` 验证：

- source review 文件存在；
- original/rebuilt 的 `status` 一致；
- original/rebuilt 的 `decision` 一致；
- original/rebuilt 的 `failed_count` 一致；
- source review digest 一致；
- `consumer_receipts` 完全一致；
- `SUMMARY_FIELDS` 全部一致；
- `RECEIPT_FIELDS` 全部一致。

`resolve_exit_code(...)` 让 CLI 在 `--require-pass` 下可以直接作为 CI/gate 使用。

## 输出产物

真实运行输出写入：

```text
e/1020/解释/receipt-check-v1020/
```

截图写入：

```text
e/1020/图片/v1020-receipt-check.png
```

JSON 是后续 index 的输入。CSV 和 HTML 都以 check rows 为主，便于定位重建不一致的字段。

## 测试覆盖

focused 测试覆盖：

- rebuildable v1019 receipt 通过 contract check；
- `granted_use` 被篡改时失败；
- source review path 丢失时失败；
- source review digest 被篡改时失败；
- CLI、locator 和五类 artifact 输出连通。

当前 focused 结果：

```text
12 passed in 16.65s
```

全量回归结果：

```text
2477 passed in 531.30s
```

source encoding hygiene 结果：

```text
status=pass
source_count=1942
clean_count=1942
syntax_error_count=0
```

## 运行证据

真实 CLI 关键结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_receipt_contract_check_v1020_passed
contract_check_ready=True
original_receipt_status=publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted
rebuilt_receipt_status=publication_receipt_index_receipt_index_receipt_v1019_lookup_receipted
original_granted_use=downstream_governance_lookup_only
rebuilt_granted_use=downstream_governance_lookup_only
original_lookup_key_count=1
rebuilt_lookup_key_count=1
original_promotion_ready=False
rebuilt_promotion_ready=False
passed_check_count=46
failed_check_count=0
```

Playwright MCP 截图确认 HTML 页面可见 `Status=pass`、`Contract=True`、`Failed=0` 和 original/rebuilt no-promotion 状态。

## 一句话总结

v1020 把 v1019 receipt 变成可复核的 contract-clean 产物，证明它能从 v1018 review 重新推导出来。

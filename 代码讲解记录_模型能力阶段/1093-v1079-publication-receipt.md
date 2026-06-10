# v1079 publication receipt 代码讲解

## 本版目标和边界

v1079 的目标是把 v1078 review 记录成一份新的 downstream lookup-only receipt。它不是新训练版本，也不是 promotion 版本，而是把上一步只读 review 变成可检索、可复用的 receipt 证据。

本版不训练模型，不增加 checkpoint，不改变质量声明，不打开 promotion。它只证明：v1078 这份 review 被可靠地接到 receipt 链路里，同时 lookup-only 的边界没变。

## 前置链路

- v1075 记录 lookup-only receipt。
- v1076 contract-check v1075 receipt。
- v1077 把 v1075 receipt 与 v1076 check 聚成 receipt index。
- v1078 review v1077 receipt index。
- v1079 记录 v1078 review 成 receipt。

这条链路里，v1078 是 review，v1079 是 receipt。

## 关键文件

### `src/minigpt/...v1079.py`

核心入口是 `build_...v1079()`。它读取 v1078 review report，并检查：

- review 文件是否存在。
- review 是否 `status=pass`。
- review decision 是否 ready。
- review summary / review body 是否都 ready。
- review status 是否仍然是 `approved_for_publication...lookup_only`。
- requested use 是否仍然是 `downstream_governance_lookup_only`。
- granted use 是否仍然 lookup-only。
- receipt index lookup 是否 ready。
- source contract check 是否 ready。
- receipt index rows 是否仍然是 1。
- source evidence rows 是否仍然是 2，且 digest 存在、状态通过。
- lookup key 是否仍然使用源 receipt-index 命名空间。
- receipt index rows 是否不进入 promotion。
- consumer boundary 和 model quality claim 是否继续保守。
- v1077/v1075/v1076/v1074/v1073 的 source path 是否都仍然存在。
- source checks 是否 clean。
- source next step 是否仍然指回 v1078 review 的 record 路线。

### `_receipt()`

`_receipt()` 把 review 包装成 receipt。它保留的核心字段包括：

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

这版仍然严格保留 `downstream_governance_lookup_only`，没有把 receipt 变成 promotion gate。

### `src/minigpt/...v1079_artifacts.py`

artifact writer 输出 JSON、CSV、TXT、Markdown 和 HTML。页面上的关键卡片是：

- `Status`
- `Receipt ready`
- `Lookup keys`
- `Evidence`
- `Use`
- `Failed`

这能一眼看到它是 lookup-only receipt，而不是被放行的生产凭证。

### `scripts/record_...v1079.py`

CLI 从 v1078 review 目录读取 JSON，生成 v1079 receipt sidecar：

```powershell
python -B scripts\record_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1079.py e\1078\解释\receipt-index-review-v1078 --out-dir e\1079\解释\receipt-v1079 --require-receipt-ready --force
```

`e/1079/解释/receipt-v1079/` 是本版最终运行证据，不是临时文件。

## 测试覆盖

`tests/test_...v1079.py` 覆盖六类场景：

- ready review 可以记录成 receipt。
- requested use 被改坏后失败。
- source review path 漂移后失败。
- source evidence status 被改坏后失败。
- CLI 在 `--require-receipt-ready` 下对坏 review 返回 `1`。
- artifact writer 和 CLI 能输出 JSON/CSV/TXT/Markdown/HTML。

这一版继续依赖 `tests/__init__.py`，确保本地 helper 导入不会再被外部同名包抢占。

## 运行证据

真实 CLI 结果：

- `status=pass`
- `receipt_ready=True`
- `receipt_status=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1079_lookup_receipted`
- `consumer_name=publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1079_lookup_reader`
- `granted_use=downstream_governance_lookup_only`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP snapshot 确认 HTML 页面显示 `Status pass`、`Receipt ready True`、`Lookup keys 1`、`Evidence 2`、`Use downstream_governance_lookup_only`、`Failed 0`，并完整展示了 source review / source receipt index / source receipt / source check / source origin review / source origin index 路径。

## 验证

- focused v1079 tests：`6 passed in 0.54s`
- full pytest：`2786 passed in 561.19s`
- source hygiene：`2179/2179 clean`
- py_compile：新增 Python 文件全部通过。

## 一句话总结

v1079 把 v1078 review 正式沉淀成 lookup-only receipt，证据链继续前推，但 promotion 仍然被严密挡住。

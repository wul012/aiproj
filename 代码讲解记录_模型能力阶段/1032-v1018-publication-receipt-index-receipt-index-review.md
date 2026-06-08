# v1018：publication receipt index receipt index review

## 本版目标和边界

v1018 的目标是审查 v1017 生成的 short-name receipt index，确认它可以进入下一步 lookup-only receipt recording。

这个 review 不是新的模型能力链，也不是 promotion gate。它只验证 v1017 index 是否仍然满足：

- lookup-only 使用边界；
- source evidence digest 存在；
- source 文件路径仍可解析；
- contract check ready；
- bounded model quality claim；
- no-promotion 标记没有被打开；
- next step 指向下一步 receipt recording。

本版不做训练、不修改 checkpoint、不比较 baseline/candidate，也不把治理证据包装成生产模型能力。

## 前置能力

v1015 记录了 v1014-reviewed receipt index 的 lookup-only receipt。v1016 证明 v1015 receipt 可以从 v1014 source review 重建。v1017 再把 v1015 receipt 和 v1016 contract check 合并成一个 digest-backed receipt index。

v1018 消费的就是 v1017 产物：

```text
e/1017/解释/receipt-index-v1017/randomized_holdout_publication_receipt_index_receipt_index_v1017.json
```

这使得后续 v1019 可以只依赖一个 review artifact，而不是直接信任 v1017 index。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_review_v1018.py`
  - 核心 review builder。
  - 读取 v1017 index，检查 lookup scope、source evidence、source paths、bounded claim 和 no-promotion。

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_review_v1018_artifacts.py`
  - 输出 JSON、CSV、Text、Markdown、HTML。
  - HTML 用于 Playwright MCP 截图，CSV 保存 check rows。

- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_v1018.py`
  - CLI 入口。
  - 支持 `--require-review-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。

- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_review_v1018.py`
  - 覆盖 ready index、lookup scope 篡改、source digest 缺失、source path 漂移、CLI 和 artifact 输出。

- `src/minigpt/randomized_holdout_publication_constants.py`
  - 新增 `RANDOMIZED_HOLDOUT_PUBLICATION_RECEIPT_INDEX_RECEIPT_INDEX_REVIEW_V1018_NEXT_STEP`。

## 核心数据结构

`review` 是本版的主要输出对象。它包含：

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

这些字段的作用是让下一步 receipt recording 可以清楚知道：它消费的是哪一个 index、这个 index 来自哪些源文件、是否仍然只允许 downstream governance lookup，以及是否仍然禁止 promotion。

`check_rows` 是 review 的审计面。每条 check 包含：

- `id`
- `status`
- `actual`
- `detail`

如果任意 check 失败，`status` 会变成 `fail`，`receipt_index_rows` 和 `source_evidence_rows` 不再作为 ready 数据输出给后续模块。

## 核心函数

`locate_receipt_index_v1018(...)` 支持传入 JSON 文件或输出目录。如果传入目录，它会自动定位 v1017 的 JSON 文件名。

`read_json_report(...)` 读取 JSON 并确保顶层是 object，避免 CLI 把数组或其他格式当成 report。

`build_randomized_holdout_publication_receipt_index_receipt_index_review_v1018(...)` 是主函数：

1. 从 v1017 report 中取出 `summary`、`receipt_index`、`receipt_index_rows` 和 `source_evidence_rows`。
2. 调用 `_checks(...)` 生成审计列表。
3. 根据失败项决定 `status` 和 `decision`。
4. 调用 `_review(...)` 生成 review 对象。
5. 汇总 `summary`、`interpretation` 和可渲染产物字段。

`_checks(...)` 保护的关键边界包括：

- v1017 index 文件必须存在；
- v1017 report 必须是 `status=pass`；
- v1017 summary 和 body 都必须 ready；
- lookup scope 与 granted use 必须仍然是 downstream governance lookup only；
- lookup row 必须只有 1 条；
- lookup key 必须使用 v1017 的短名 namespace；
- source evidence 必须是 2 条，且每条有 SHA-256，状态为 pass；
- v1015 receipt、v1016 receipt check、v1014 source review、v1013 source receipt index 都必须仍存在；
- consumer boundary 和 model quality claim 不能扩大；
- `promotion_ready` 和 `approved_for_promotion` 必须保持 False；
- v1017 source checks 必须 clean；
- v1017 next step 必须指向 v1018 review。

`resolve_exit_code(...)` 让 CLI 可以按不同严格度退出：

- `--require-review-ready`：review 不 ready 返回 1；
- `--require-lookup-ready`：lookup 不 ready 返回 1；
- `--require-promotion-ready`：promotion 不 ready 返回 1。

因为本项目当前明确禁止 promotion，`--require-promotion-ready` 对真实 v1018 证据会返回 1，这是预期行为。

## 输出产物

JSON 是后续模块的主要消费对象。CSV 保存 check rows，方便快速查看失败项。Text 用于命令行摘要。Markdown 和 HTML 用于人工审查与截图证据。

真实运行输出写入：

```text
e/1018/解释/receipt-index-review-v1018/
```

截图写入：

```text
e/1018/图片/v1018-receipt-index-review.png
```

这些产物是 lookup-only evidence，不是训练结果，也不是模型上线凭证。

## 测试覆盖

focused 测试覆盖五类场景：

- ready index 通过 review，并保留 `review_ready=True`、`lookup_ready=True`、`contract_check_ready=True`、`promotion_ready=False`；
- `lookup_scope` 改成 `production_promotion` 时失败；
- source evidence digest 缺失时失败；
- source receipt path 漂移时失败；
- CLI、locator 和五类 artifact 输出都连通。

当前 focused 测试结果：

```text
9 passed in 11.65s
```

全量回归结果：

```text
2465 passed in 442.07s
```

source encoding hygiene 结果：

```text
status=pass
source_count=1934
clean_count=1934
syntax_error_count=0
```

## 运行证据

真实 CLI 关键结果：

```text
status=pass
decision=randomized_holdout_publication_receipt_index_receipt_index_review_v1018_ready
review_ready=True
review_status=approved_for_publication_receipt_index_receipt_index_lookup_only
receipt_index_row_count=1
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=22
failed_check_count=0
```

Playwright MCP 截图确认 HTML 页面可见 `Status=pass`、`Review ready=True`、`Failed=0`、source receipt、source check、source review 和 source receipt index。

## 一句话总结

v1018 在 v1017 receipt index 和下一步 receipt recording 之间加了一层短名 review，把 lookup-only 证据链再审一次，同时继续锁住 no-promotion 边界。

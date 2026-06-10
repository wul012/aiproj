# v1073 publication receipt index

## 本版目标与边界

v1073 的目标是把 v1071 receipt 和 v1072 receipt contract check 编成一个 digest-backed lookup index。它不是新训练版本，不改变 checkpoint，也不把模型能力结论升级为生产可用；它只把“收据产物 + 收据复核产物”收束成一个可检索、可复核、可继续 review 的索引入口。

这版承接 v1071 和 v1072：

1. v1071 记录 v1070 review，形成 downstream lookup-only receipt。
2. v1072 重新构建 v1071 receipt，验证 contract check 仍然 pass。
3. v1073 把这两个源产物写进 receipt index，并记录各自 digest。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1073.py`
  - 核心 index builder。
  - 输入 v1071 receipt 与 v1072 check，验证 source path、source digest、lookup-only use、contract check ready、no-promotion 边界和 next-step 路由。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1073_artifacts.py`
  - 输出 JSON / CSV / TXT / Markdown / HTML。
  - CSV 面向后续索引消费，HTML 面向截图和人工审阅。
- `scripts/build_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1073.py`
  - CLI 入口。
  - 支持 `--receipt`、`--receipt-check`、`--require-index-ready`、`--require-lookup-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1073.py`
  - 覆盖 ready index、granted_use 篡改、contract check not ready、artifact/CLI wiring。
- `e/1073/解释/receipt-index-v1073/`
  - 本版真实 CLI 证据目录。
- `e/1073/图片/v1073-receipt-index.png`
  - Playwright MCP 运行截图。

## 核心数据结构

### `receipt_index`

`receipt_index` 是本版核心交接对象，包含：

- `receipt_index_id`
- `lookup_scope`
- `receipt_index_rows`
- `source_evidence_rows`
- `next_step`

其中 `lookup_scope` 固定为 `downstream_governance_lookup_only`，说明这个索引仍然只服务治理链检索，不允许作为 production promotion 证据。

### `receipt_index_rows`

当前只有一行，记录：

- lookup key
- receipt id
- receipt status
- granted use
- contract check ready
- promotion ready

它让后续 review 不需要重新解析 receipt 和 check 的完整 JSON，只要读取索引行即可判断这次 lookup 是否可用。

### `source_evidence_rows`

本版记录两个 source evidence：

- v1071 receipt
- v1072 receipt contract check

每行都包含 `kind`、`path`、`sha256`、`status`。这组字段是索引防篡改的核心：路径证明源文件在哪里，digest 证明源文件内容没有悄悄变化。

## 运行流程

1. CLI 接收 `--receipt` 和 `--receipt-check`。
2. `locate_receipt_v1073()` 定位 v1071 receipt JSON。
3. `locate_receipt_check_v1073()` 定位 v1072 check JSON。
4. builder 读取 receipt summary、receipt body 和 check summary。
5. `_checks()` 校验 readiness、lookup-only use、contract check ready、source path、digest 和 next-step。
6. `_index()` 生成索引行和 source evidence 行。
7. artifacts 模块输出 JSON / CSV / TXT / Markdown / HTML。
8. `resolve_exit_code()` 根据 `--require-index-ready` 和 `--require-lookup-ready` 返回自动化退出码。

## 测试覆盖

focused v1073 测试结果：

```text
4 passed in 0.80s
```

测试保护点包括：

- ready receipt + ready contract check 能生成 ready index。
- receipt 的 `granted_use` 被篡改为 production promotion 会失败。
- contract check 不 ready 会失败。
- CLI、locator、artifact writer 和 HTML/Markdown/TXT renderer 同源。

- full pytest: `2754 passed in 835.31s`
- source hygiene: `status=pass`, `source_count=2154`, `clean_count=2154`

## 运行证据

真实 CLI 输出确认：

- `status=pass`
- `index_ready=True`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=25`
- `failed_check_count=0`

Playwright MCP 截图：

- `e/1073/图片/v1073-receipt-index.png`

## 一句话总结

v1073 把 v1071 receipt 与 v1072 contract check 收束为可检索、带 digest、防篡改的索引证据，为下一步 review 提供了稳定入口。

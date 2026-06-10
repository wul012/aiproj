# v1074 publication receipt index review

## 本版目标与边界

v1074 的目标是审阅 v1073 receipt index，确认这份 index 可以作为下一步 receipt recording 的 lookup-only 输入。它不训练模型，不改变 checkpoint，不把治理链证据解释成生产模型质量；它只审阅 v1073 的索引行、source evidence、digest 和 no-promotion 边界。

这版承接 v1073：

1. v1073 把 v1071 receipt 与 v1072 contract check 编成 digest-backed receipt index。
2. v1074 读取这个 index，验证 index ready、lookup ready、contract check ready、source evidence digest 和 next-step routing。
3. v1074 输出 review，供后续 receipt recording 使用。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1074.py`
  - 核心 review builder。
  - 检查 v1073 index 的 row、source evidence、digest、lookup-only use、contract readiness 和 no-promotion 字段。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1074_artifacts.py`
  - 输出 JSON / CSV / TXT / Markdown / HTML。
- `scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1074.py`
  - CLI 入口。
  - 支持 `--require-review-ready`、`--require-lookup-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1074.py`
  - 覆盖 ready review、source evidence drift、lookup readiness、artifact/CLI wiring 等路径。
- `e/1074/解释/receipt-index-review-v1074/`
  - 本版真实 CLI 证据。
- `e/1074/图片/v1074-receipt-index-review.png`
  - Playwright MCP 截图证据。

## 核心数据结构

### `review`

`review` 是本版核心输出对象，保存：

- review readiness
- review status
- granted use
- lookup readiness
- contract check readiness
- source receipt path
- source receipt check path
- source review path
- source receipt index path
- next step

### `summary`

`summary` 面向 CLI、README 和 HTML 展示，核心字段包括：

- `review_ready`
- `review_status`
- `receipt_index_row_count`
- `lookup_key_count`
- `source_evidence_count`
- `lookup_ready`
- `contract_check_ready`
- `promotion_ready`
- `next_step`
- `passed_check_count`
- `failed_check_count`

### `check_rows`

`check_rows` 是本版防回归的关键，覆盖：

- v1073 index 文件存在
- digest 与源文件一致
- index ready
- lookup-only use
- source evidence count
- source evidence status
- contract check ready
- promotion blocked
- next-step 指向 receipt recording

## 运行流程

1. CLI 接收 v1073 receipt index JSON 或目录。
2. `locate_receipt_index_v1074()` 定位 v1073 index JSON。
3. `build_..._review_v1074()` 读取 index、summary 和 source evidence。
4. `_checks()` 校验 lookup-only、source evidence、digest、contract readiness 和 no-promotion。
5. `_review()` 生成 review 对象。
6. artifacts 模块输出 JSON / CSV / TXT / Markdown / HTML。
7. `resolve_exit_code()` 根据 `--require-review-ready` 和 `--require-lookup-ready` 决定自动化退出码。

## 测试覆盖

focused v1074 测试结果：

```text
5 passed in 0.65s
```

测试保护点包括：

- ready v1073 index 能生成 ready review。
- source evidence digest 漂移会失败。
- lookup ready 被破坏会失败。
- CLI、locator、renderer 和 artifact writer 同源。

- full pytest: `2759 passed in 503.25s`
- source hygiene: `status=pass`, `source_count=2158`, `clean_count=2158`

## 运行证据

真实 CLI 输出确认：

- `status=pass`
- `review_ready=True`
- `receipt_index_row_count=1`
- `lookup_key_count=1`
- `source_evidence_count=2`
- `lookup_ready=True`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=22`
- `failed_check_count=0`

Playwright MCP 截图：

- `e/1074/图片/v1074-receipt-index-review.png`

## 一句话总结

v1074 把 v1073 的 receipt index 审阅成可继续交接的 lookup-only review，为下一步 receipt recording 提供了稳定、带 digest 的输入。

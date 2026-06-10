# v1072 publication receipt contract check

## 本版目标与边界

v1072 的目标很明确：把 v1071 的 receipt 当作 contract-check 输入，验证它是否仍然能从 v1070 的 source review 重新推导出来。它不新增训练链，不改 checkpoint，不放大模型能力，只做一层轻量、可复核的契约核对。

这一版承接的是 v1071 的 receipt recording 链路。v1071 负责把 v1070 review 记录成 lookup-only receipt；v1072 则反过来检查这张 receipt 是否还能从源 review 重建出来，防止 handoff artifact 被篡改、路径丢失，或者 next-step 与来源结果不一致。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1072.py`
  - 核心 contract-check builder。
  - 读取 v1071 receipt，找到源 v1070 review，重新调用 v1071 builder 重建 receipt，再逐字段对比。
- `src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1072_artifacts.py`
  - 负责把 check report 导出为 JSON / CSV / TXT / Markdown / HTML。
  - HTML 是后续截图和人工审阅的主入口。
- `scripts/check_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_v1072.py`
  - CLI 入口。
  - 支持 `--out-dir`、`--require-pass`、`--force`，适合自动化 gate 和本地复核。
- `tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_check_v1072.py`
  - 覆盖正常通过、篡改 granted_use、缺失源 review、篡改 digest、`--require-pass` 返回码等场景。
- `e/1072/解释/receipt-check-v1072/`
  - 本版最终 CLI 证据目录。
- `e/1072/图片/v1072-receipt-check.png`
  - Playwright 截图证据。

## 核心数据结构

### 输入对象 `receipt_report`

`receipt_report` 是 v1071 receipt 的 JSON 读入结果。builder 会从里面取：

- `summary`
- `receipt`
- `receipt_index_review_path`
- `receipt_index_review_sha256`

### 输出对象

`build_..._v1072()` 返回一个总报告，核心字段是：

- `status`
- `decision`
- `failed_count`
- `issues`
- `source_receipt_index_review`
- `original_summary`
- `rebuilt_summary`
- `original_receipt`
- `rebuilt_receipt`
- `check_rows`
- `summary`
- `interpretation`

其中：

- `original_*` 来自输入 receipt
- `rebuilt_*` 来自用源 review 重新调用 v1071 builder 的结果
- `check_rows` 是逐项契约对比的最小单元
- `summary` 是给 CLI / HTML / 截图看的汇总视图

### `summary` 里的关键字段

- `contract_check_ready`
- `source_receipt_index_review`
- `original_receipt_status`
- `rebuilt_receipt_status`
- `original_granted_use`
- `rebuilt_granted_use`
- `original_lookup_key_count`
- `rebuilt_lookup_key_count`
- `original_promotion_ready`
- `rebuilt_promotion_ready`
- `next_step`
- `passed_check_count`
- `failed_check_count`

这组字段的价值在于：它不只告诉你“pass 了”，还告诉你 pass 的依据到底是哪一组 source-review / receipt / summary 对齐关系。

## 运行流程

1. CLI 接收 receipt JSON 或输出目录。
2. `locate_receipt_v1072()` 定位 v1071 receipt。
3. `read_json_report()` 读取 JSON。
4. `build_..._v1072()` 提取原始 summary / receipt。
5. `_resolve_source_review_path()` 找到源 review。
6. `_rebuild_receipt()` 重新调用 v1071 builder，得到重建结果。
7. `_checks()` 比对 status、decision、failed_count、digest、consumer receipts，以及 summary / receipt 的逐字段值。
8. `_summary()` 汇总 pass/fail、count、next_step。
9. artifacts 模块导出 JSON / CSV / TXT / Markdown / HTML。
10. CLI 根据 `--require-pass` 决定退出码。

## 测试覆盖

这版测试不是只看“能不能跑”，而是看契约是否真的成立：

- 正常样本应当 `status=pass`
- 篡改 `granted_use` 应触发失败
- 删除或改错 `source_review` 应触发失败
- 篡改 digest 应触发失败
- `--require-pass` 在失败时必须返回 `1`
- artifact 文件名和 CLI 输出必须同源

实际结果：

- focused v1071 tests: `6 passed in 0.62s`
- focused v1072 tests: `6 passed in 0.33s`
- full pytest: `2750 passed in 581.69s`
- source hygiene: `status=pass`, `source_count=2150`, `clean_count=2150`

## 运行证据

本版的真实 CLI 输出确认了：

- `status=pass`
- `failed_count=0`
- `contract_check_ready=True`
- `passed_check_count=46`
- `source_receipt_index_review` 指向 v1070 review

Playwright 截图证据位于：

- `e/1072/图片/v1072-receipt-check.png`

## 一句话总结

v1072 把 v1071 这张 receipt 从“可读的产物”推进成了“可复核的 contract-check 产物”，让 receipt 链路真正多了一层防篡改和可重建的证据。

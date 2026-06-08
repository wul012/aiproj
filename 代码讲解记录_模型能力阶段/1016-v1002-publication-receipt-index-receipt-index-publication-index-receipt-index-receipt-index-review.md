# v1002 publication receipt index receipt index publication index receipt index receipt index review

本版目标是复核 v1001 receipt-index-receipt index，让它在进入下一层 receipt 记录之前先经过只读 review。它解决的问题是：v1001 已经生成 lookup index，但 receipt 记录前还需要确认索引行、source evidence、来源路径和 no-promotion 边界没有漂移。

本版不训练模型，不修改 checkpoint，不扩大模型质量声明，也不做 production promotion。它只是 review v1001 的治理索引，并把下一步路由到 receipt 记录。

## 前置路线

v999 记录 receipt。v1000 contract-check v999 receipt。v1001 将 v999 receipt 和 v1000 check 组合为 lookup-only index。v1002 在 v1001 之后做 review，确认这份 index 能被 downstream receipt 记录消费。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_review_v1002.py`
  - v1002 核心 review。读取 v1001 index report，执行 25 项检查，输出 review body 和 summary。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_review_v1002_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1002.py`
  - CLI 入口，支持 JSON 或输出目录，支持 `--require-review-ready` 和 `--require-receipt-index-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_review_v1002.py`
  - 覆盖正常 review、digest 篡改、lookup scope 篡改、body/row 路径漂移、CLI 失败退出和输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v1002 下一步常量：`record_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_v1002`。
- `src/minigpt/__init__.py`
  - 暴露 v1002 build/write 包级懒加载入口。

## 核心数据结构

v1002 输入是 v1001 index report。关键字段包括：

- `summary`
  - 提供 index ready、lookup scope、lookup key count、contract check ready、promotion ready 等摘要。
- `receipt_index`
  - 保存 `receipt_index_rows`、`source_evidence_rows`、`receipt_path`、`receipt_check_path` 和 next step。
- `receipt_index_rows`
  - 必须只有一条，并且 lookup key 使用 `publication-index-receipt-index-receipt:` 命名空间。
- `source_evidence_rows`
  - 必须有两条，均为 pass，并带 SHA-256 digest。

v1002 输出 `review` 对象，核心字段包括：

- `review_ready`
- `review_status`
- `receipt_index_path`
- `receipt_index_id`
- `receipt_index_row_count`
- `source_evidence_count`
- `lookup_keys`
- `receipt_index_ready`
- `lookup_ready`
- `contract_check_ready`
- `promotion_ready`
- `approved_for_promotion`
- `source_receipt_path`
- `source_receipt_check_path`
- `next_step`

## 检查逻辑

`_checks()` 保护以下内容：

- v1001 index 文件存在且 `status=pass`。
- v1001 decision 和 ready flag 正确。
- lookup scope 与 granted use 都是 `downstream_governance_lookup_only`。
- lookup ready 和 contract check ready 都为 true。
- 只有一条 index row，lookup key 命名空间正确。
- index row 不允许 promotion。
- source evidence 数量为 2，状态为 pass，digest 是 SHA-256，文件仍存在。
- receipt path/check path 在 body 和 row 中一致。
- source review 和 source receipt index 路径仍存在。
- consumer boundary 与 model quality claim 保持治理边界。
- promotion 和 approved_for_promotion 都是 false。
- source failed check count 为 0。
- v1001 next step 正确路由到 v1002 review。

这些检查让后续 receipt 记录可以直接消费 review，而不用重新解释 v1001 的每个字段。

## 运行证据

真实运行命令：

```powershell
python scripts\review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1002.py e\1001\解释\receipt-index-v1001 --out-dir e\1002\解释\review-v1002 --require-review-ready --require-receipt-index-ready --force
```

输出显示 `status=pass`、`review_ready=True`、`review_status=approved_for_publication_index_receipt_index_receipt_index_receipt_lookup_only`、`lookup_key_count=1`、`source_evidence_count=2`、`contract_check_ready=True`、`promotion_ready=False`、`failed_check_count=0`、`passed_check_count=25`。

运行截图位于 `e/1002/图片/v1002-review.png`，页面显示 pass 状态、review ready、receipt index ready、lookup keys 和 failed 计数。

## 测试覆盖

测试覆盖：

- 正常 v1001 index 可以通过 review。
- source evidence digest 篡改会失败。
- lookup scope 被改为 production promotion 会失败。
- body 与 row 的 receipt path 不一致会失败。
- CLI `--require-review-ready` 在失败报告下返回 1。
- 输出测试覆盖 JSON/CSV/TXT/Markdown/HTML。

收口验证还包括：

- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v1002`
  - `status=pass`、`bom_count=0`、`syntax_error_count=0`、`compatibility_error_count=0`。
- `git diff --check`
  - 通过。
- `python -m pytest -q -o cache_dir=runs/pytest-cache-v1002`
  - `2382 passed in 381.27s`。

## 一句话总结

v1002 把 v1001 的 lookup-only index 推进到“已 review、可记录 receipt”的状态，同时继续保持模型质量声明和生产推广边界不变。

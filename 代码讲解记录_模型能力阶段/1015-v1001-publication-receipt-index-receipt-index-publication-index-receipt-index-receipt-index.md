# v1001 publication receipt index receipt index publication index receipt index receipt index

本版目标是把 v999 receipt 和 v1000 contract check 组合成新的 lookup-only receipt index。它解决的问题是：v999 已经记录了 downstream receipt，v1000 已经证明该 receipt 可从源 review 重建，但后续治理模块还缺一个稳定索引入口来查找这组证据。

本版不训练模型，不修改 checkpoint，不扩大模型能力声明，也不做 production promotion。它只是把“已记录 + 已复核”的 receipt 证据登记成可查索引。

## 前置路线

v998 复核 v997 receipt index。v999 基于 v998 review 记录 downstream receipt。v1000 从 v998 review 重建 v999 receipt，并逐字段确认 receipt 没有漂移。v1001 站在 v1000 之后，把 v999 receipt 和 v1000 check 合并登记为一个 receipt-index-receipt 索引，为下一步 review 提供固定输入。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001.py`
  - v1001 核心 builder。它读取 receipt report 和 receipt check report，执行 24 项检查，并输出一个 lookup-only receipt index。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。CSV 保存索引行，HTML 用于运行截图。
- `scripts/build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001.py`
  - CLI 入口，支持 receipt/check 目录或 JSON 文件，支持 `--require-index-ready`、`--require-lookup-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001.py`
  - 覆盖正常索引、granted use 篡改、contract check 不 ready、输出渲染和 CLI。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v1001 下一步常量：`review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001`。
- `src/minigpt/__init__.py`
  - 暴露 v1001 build/write 包级懒加载入口。

## 核心数据结构

v1001 输出包含：

- `receipt_index_rows`
  - 后续模块消费的查询行。
- `source_evidence_rows`
  - v999 receipt 和 v1000 contract check 的路径、SHA-256 与状态。
- `receipt_index`
  - 结构化索引体，包括 `index_ready`、`lookup_scope`、`lookup_key_count`、`contract_check_ready`、`promotion_ready` 和 `next_step`。
- `summary`
  - 供 CLI 和 README 摘要消费的稳定字段。

索引 lookup key 使用：

```text
publication-index-receipt-index-receipt:<receipt_id>
```

这个命名空间和 v997 的 `publication-index-receipt:` 区分开，表示这里索引的是“receipt index receipt”这一层，而不是更早的 publication index receipt。

## 检查逻辑

`_checks()` 做 24 项检查，重点保护：

- v999 receipt 文件存在且 `status=pass`。
- v999 decision 和 ready flag 指向 receipt ready。
- v999 receipt status 保持 `publication_index_receipt_index_lookup_receipted`。
- v1000 check 文件存在、`status=pass`、decision 为 contract check passed。
- original/rebuilt receipt status 一致。
- summary、receipt body、original check、rebuilt check 的 granted use 都是 `downstream_governance_lookup_only`。
- lookup key 数量为 1。
- source evidence 数量为 2。
- source receipt index review、source receipt index、source receipt、source receipt check 路径仍然存在。
- consumer boundary 仍为 `governance_lookup_only`。
- model quality claim 仍为 `bounded_randomized_target_hidden_holdout_claim_only`。
- promotion 相关字段全部为 false。
- v999/v1000 的 next step 正确衔接到 v1001。

这些检查不是证明模型更强，而是证明治理证据没有被改成生产推广或模型质量扩张用途。

## 运行证据

真实运行命令：

```powershell
python scripts\build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001.py --receipt e\999\解释\publication-receipt-index-receipt-index-publication-index-receipt-index-receipt-v999 --receipt-check e\1000\解释\receipt-index-receipt-check-v1000 --out-dir e\1001\解释\receipt-index-v1001 --require-index-ready --require-lookup-ready --force
```

输出显示 `status=pass`、`index_ready=True`、`lookup_scope=downstream_governance_lookup_only`、`lookup_key_count=1`、`contract_check_ready=True`、`promotion_ready=False`、`failed_check_count=0`、`passed_check_count=24`。

运行截图位于 `e/1001/图片/v1001-receipt-index.png`。截图页面显示 pass 状态、索引 ready、lookup key 数量、source evidence 和 checks 表格。

## 测试覆盖

测试覆盖：

- 正常 v999 receipt + v1000 check 可以生成 ready index。
- 篡改 `summary.granted_use` 会让 `granted_use_lookup_only` 检查失败。
- 将 v1000 `contract_check_ready` 改成 false 会让 contract check 失败。
- CLI 可以从输出目录定位 JSON，并在 `--require-index-ready --require-lookup-ready` 下成功。
- 输出测试覆盖 JSON/CSV/TXT/Markdown/HTML。

聚焦测试命令：

```powershell
python -m pytest tests\test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_v1001.py -q -o cache_dir=runs/pytest-cache-v1001-focus
```

收口验证还包括：

- `python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v1001`
  - `status=pass`、`bom_count=0`、`syntax_error_count=0`、`compatibility_error_count=0`。
- `git diff --check`
  - 通过。
- `python -m pytest -q -o cache_dir=runs/pytest-cache-v1001`
  - `2376 passed in 279.76s`。

## 一句话总结

v1001 把 v999 receipt 和 v1000 contract check 从“独立证据”推进为“可查索引”，让后续 review 层能稳定消费这组 lookup-only 治理证据。

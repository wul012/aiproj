# v1005 publication receipt index receipt index publication index receipt index receipt index receipt index

本版目标是把 v1003 receipt 和 v1004 contract check 打包成下一层 lookup-only receipt index。它解决的问题是：v1004 已经证明 v1003 receipt 可以从源 v1002 review 重建，但后续治理链还需要一个索引入口，把 receipt 与 check 放到同一个可查表里。

本版不训练模型，不生成 checkpoint，不扩大模型质量声明，不允许 production promotion。它只建立 lookup-only index，并把下一步路由到 review。

## 前置路线

v1003 记录 lookup-only downstream receipt。v1004 从 v1003 记录的 source v1002 review 重建 receipt，并逐字段确认一致。v1005 在这两份证据之后做索引：一行 index row 指向 v1003 receipt，一组 source evidence row 同时记录 v1003 receipt 和 v1004 check 的 digest。

这样后续版本不用分别解析 receipt 和 check，只需要读取 v1005 index，就能知道它们已经成对通过。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005.py`
  - v1005 核心 index builder。读取 receipt 与 contract check，执行 24 项检查，生成 index row、source evidence row、summary 和 interpretation。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005.py`
  - CLI 入口，支持 `--receipt`、`--receipt-check`、`--require-index-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005.py`
  - 覆盖正常 index、granted use 漂移、contract check 不 ready、CLI 和输出渲染。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v1005 next step：`review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005`。
- `src/minigpt/__init__.py`
  - 暴露 v1005 build/write 懒加载入口。
- `e/1005/解释/receipt-index-v1005/*`
  - 本版真实运行证据。
- `e/1005/图片/v1005-receipt-index.png`
  - Playwright MCP 截图证据。

## 输入输出

v1005 输入两份报告：

- v1003 receipt report
- v1004 contract check report

CLI 可以接收 JSON 文件或输出目录。`locate_receipt_v1005()` 和 `locate_receipt_check_v1005()` 会把目录解析为固定 JSON 文件名，避免调用者手写长文件名。

输出 report 主要包含：

- `receipt_index_rows`
  - 一行 lookup row，指向 v1003 receipt。
- `source_evidence_rows`
  - 两行 digest-backed source evidence，分别记录 receipt 和 receipt_check。
- `receipt_index`
  - index body，包含 lookup scope、source paths、contract readiness、promotion flags 和 next step。
- `summary`
  - 面向 README、CLI、后续 review 的稳定摘要。
- `check_rows`
  - 24 项检查。

## lookup key

本版 lookup key 使用：

```text
publication-index-receipt-index-receipt-index-receipt:<receipt_id>
```

这个命名空间不是随便加长。v1001 索引的是 v999 receipt，所以使用 `publication-index-receipt-index-receipt:`。v1005 索引的是 v1003 这一层 receipt-index-receipt receipt，因此前缀升级为 `publication-index-receipt-index-receipt-index-receipt:`。

测试中显式断言这个前缀，防止后续模板迁移时退回旧命名空间。

## 检查逻辑

`_checks()` 保护以下内容：

- receipt 文件和 receipt check 文件存在。
- v1003 receipt status 为 pass。
- v1003 decision 和 ready flag 正确。
- v1003 receipt status 是 `publication_index_receipt_index_receipt_index_lookup_receipted`。
- v1004 check status 为 pass。
- v1004 decision 为 contract check passed。
- v1004 summary 标记 `contract_check_ready=True`。
- receipt status 在 receipt 与 check 的 original/rebuilt 字段中一致。
- granted use 在 summary、receipt、check original/rebuilt 中都保持 downstream lookup only。
- lookup key count 在 receipt、check original/rebuilt 和 receipt body 中一致且等于 1。
- receipt index row count 等于 1。
- source evidence count 等于 2。
- v1003 记录的 source review、source receipt index、source receipt、source check 文件仍存在。
- consumer boundary 是 governance lookup only。
- model quality claim 仍是 bounded randomized target hidden holdout claim。
- promotion 和 approved_for_promotion 全部保持 false。
- v1003/v1004 failed check count 都是 0。
- v1003 next step 指向 check，v1004 next step 指向 index。

这些检查让 v1005 不是简单复制两个文件路径，而是证明 receipt 与 check 仍然匹配。

## Artifact 输出

输出层生成五类文件：

- JSON：后续 review 的机器输入。
- CSV：一行 receipt index row。
- TXT：终端摘要。
- Markdown：归档审阅。
- HTML：浏览器审阅和截图。

HTML 页面展示：

- Summary cards：status、index ready、lookup key count、contract、evidence、failed count。
- Receipt Index Rows：lookup key、receipt id、receipt status、use、contract flag、promotion flag。
- Source Evidence：receipt 与 check 的 SHA-256 digest。
- Checks：24 项检查。

这些产物都是最终证据，不是临时调试文件。

## 测试覆盖

测试覆盖：

- ready v1003 receipt + v1004 check 可以生成 pass index。
- summary 中的 ready flag、lookup key count、source evidence count、receipt status、granted use、contract readiness、promotion flag 和 next step 都符合预期。
- lookup key 前缀必须是 `publication-index-receipt-index-receipt-index-receipt:`。
- granted use 改成 `production_promotion` 会失败。
- contract check ready 被改成 false 会失败。
- CLI 可以通过目录输入 receipt/check 并生成完整产物。
- 输出层覆盖 JSON/CSV/TXT/Markdown/HTML。

focused 测试结果：

```text
4 passed in 5.96s
```

source encoding 结果：

```text
status=pass
source_count=1882
bom_count=0
syntax_error_count=0
compatibility_error_count=0
```

最终收口还包括：

```text
git diff --check: pass, only Git line-ending warnings
full pytest: 2397 passed in 346.04s (0:05:46)
```

## 运行证据

真实运行命令：

```powershell
python scripts\build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_receipt_index_receipt_index_receipt_index_v1005.py --receipt e\1003\解释\receipt-v1003 --receipt-check e\1004\解释\receipt-check-v1004 --out-dir e\1005\解释\receipt-index-v1005 --require-index-ready --require-lookup-ready --force
```

输出显示：

- `status=pass`
- `index_ready=True`
- `lookup_key_count=1`
- `receipt_status=publication_index_receipt_index_receipt_index_lookup_receipted`
- `granted_use=downstream_governance_lookup_only`
- `source_evidence_count=2`
- `contract_check_ready=True`
- `promotion_ready=False`
- `passed_check_count=24`
- `failed_check_count=0`

截图位于 `e/1005/图片/v1005-receipt-index.png`，页面显示 pass、index ready、lookup keys、contract、evidence 和 failed 计数。

## 一句话总结

v1005 把 v1003 receipt 与 v1004 contract check 合并为下一层 lookup-only index，让治理链从“单份 receipt 已验证”推进到“receipt/check 成对可检索”。

# v993 publication receipt index receipt index publication index

本版目标是把 v991 lookup-only publication 和 v992 contract check 合并成一个 publication index。它解决的是后续模块不应同时手动追踪两个源文件的问题：v993 用一条 `publication-index:` lookup row 和两条 source evidence 把发布对象与复核结果绑定起来。

本版不训练模型，不改 checkpoint，不扩大模型质量声明，不允许 production promotion。

## 前置路线

v991 发布 v990 review 认可的 lookup-only publication。v992 重新从 v990 review 构建 publication，并证明 original/rebuilt 的稳定字段一致。v993 只在这两者都通过时创建 index。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993.py`
  - 核心 index builder。检查 v991/v992 一致性，并生成 `publication_index`。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993.py`
  - CLI 入口，支持 `--require-index-ready` 和 `--require-lookup-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993.py`
  - 覆盖 ready index、published use 篡改、contract check 不 ready、CLI 失败码和输出写入。

## 核心结构

`publication_index` 包含：

- `index_ready`
- `publication_index_id`
- `lookup_scope=downstream_governance_lookup_only`
- `publication_index_rows`
- `source_evidence_rows`
- `publication_path`
- `publication_check_path`
- `published_use=downstream_governance_lookup_only`
- `promotion_ready=False`
- `approved_for_promotion=False`
- `next_step=review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993`

其中 `source_evidence_rows` 对 v991 publication 和 v992 check 计算 SHA-256，后续 review 可以确认源文件没有漂移。

## 检查范围

v993 检查 publication/check 文件存在、v991 publication ready、v992 contract check ready、publication status 与 check 中 original/rebuilt status 一致、published use 仍是 lookup only、lookup key 只有一条、source evidence 为两条、source review/index/receipt/check 路径仍存在、bounded claim 和 no-promotion 字段不变。

真实运行输出显示 `status=pass`、`index_ready=True`、`source_evidence_count=2`、`failed_check_count=0`、`passed_check_count=23`。

## 运行证据

运行证据写入 `e/993/解释/说明.md` 和 `e/993/解释/publication-receipt-index-receipt-index-publication-index-v993/`。Playwright MCP 截图保存在 `e/993/图片/`，证明 HTML 报告可打开并展示 index、source evidence 和 checks 表。

## 一句话总结

v993 把 v991/v992 发布证据合并成 lookup-only publication index，仍然不开放生产提升。

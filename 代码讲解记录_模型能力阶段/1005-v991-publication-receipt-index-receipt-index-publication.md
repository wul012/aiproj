# v991 baseline publication receipt index receipt index publication

本版目标是把 v990 已经审阅通过的 receipt index receipt index 发布成一个 downstream lookup-only publication。它解决的是 review 之后的“可消费入口”问题：下游不再直接读 review 报告，而是读一个明确写着发布状态、发布用途、source evidence、lookup key 和 no-promotion 边界的 publication artifact。

本版不做模型训练，不更新 checkpoint，不扩大 randomized holdout 的模型质量声明，也不把 `promotion_ready` 改成 true。它仍然属于模型能力阶段中的治理证据链：把真实 tiny 训练路线中已经形成的 bounded claim 做成可审计的只读 publication。

## 前置路线

v987 记录了 v986 review 认可的 lookup-only receipt。v988 从 v986 review 重新构建 receipt 并做 contract check。v989 把 receipt 和 check 合并成 receipt index。v990 再审阅这个 index，确认一条 `receipt-index-receipt:` lookup key、两条 source evidence、digest、source receipt/check 路径、blocked uses 和 no-promotion 边界都成立。

v991 接在 v990 的 `next_step=publish_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v990` 后面。只有当 v990 review 明确为 `approved_for_publication_receipt_index_receipt_index_publication_lookup_only` 时，本版才允许生成 ready publication。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.py`
  - 核心 builder。读取 v990 review，抽取 `summary`、`review`、`receipt_index_rows` 和 `source_evidence_rows`，执行发布前检查，然后生成 publication、summary 和 interpretation。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_artifacts.py`
  - 输出层。负责把 report 写成 JSON、CSV、TXT、Markdown 和 HTML，并把检查表渲染成浏览器可读页面。
- `scripts/publish_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v991.py`
  - CLI 入口。支持输入 v990 JSON 或输出目录，支持 `--require-publication-ready`、`--require-lookup-ready`、`--require-promotion-ready` 和 `--force`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991.py`
  - 单测。覆盖 ready publication、review status 漂移、source receipt 缺失、CLI 失败码和五类输出。
- `e/991/解释/publication-receipt-index-receipt-index-publication-v991/*`
  - 本版运行证据。它是最终 evidence，不是临时文件。
- `e/991/图片/v991-randomized-holdout-publication-receipt-packet-index-publication-receipt-index-receipt-index-publication.png`
  - Playwright MCP 截图证据，证明 HTML 报告可正常打开和渲染。

## 核心数据结构

builder 输出的顶层 report 包含：

- `status`：所有检查通过时为 `pass`。
- `decision`：通过时为 `randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991_ready`。
- `receipt_index_review_path`：指向 v990 review JSON。
- `source_receipt_index_review_summary` 和 `source_receipt_index_review`：保留 v990 的原始 summary/body，便于下游复核。
- `receipt_index_rows`：来自 v990 review 的 lookup rows，本版要求只有一条，并且 key 必须以 `receipt-index-receipt:` 开头。
- `source_evidence_rows`：来自 v990 review 的 source evidence，本版要求两条、状态均为 pass、digest 均为 SHA-256，且文件仍存在。
- `publication`：本版新增的可消费发布对象。
- `summary`：供 CLI、README、HTML 和后续 check 快速读取的压缩字段。

`publication` 的关键字段包括：

- `publication_ready=True`
- `publication_status=published_for_publication_receipt_index_receipt_index_lookup_only`
- `published_use=downstream_governance_lookup_only`
- `lookup_keys=[...]`
- `source_receipt_path`
- `source_receipt_check_path`
- `blocked_uses=["production_promotion", "model_quality_expansion", "training_data_claim_expansion"]`
- `promotion_ready=False`
- `approved_for_promotion=False`
- `next_step=check_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_v991`

这些字段的作用是把“允许下游读取”和“禁止生产提升”同时写在同一个 artifact 里，避免后续模块只看到了 ready 状态，却误解为可以放大模型能力声明。

## 核心检查

本版 `_checks` 一共保护 24 个条件。重要的几类是：

- 源 review 必须存在、`status=pass`、decision 必须是 v990 ready。
- review summary 和 body 都必须 ready。
- review status 必须是 lookup-only publication approval。
- v990 指向的 receipt index、source receipt 和 source receipt check 必须还存在。
- `receipt_ready`、`lookup_ready`、`contract_check_ready` 必须同时为 true。
- lookup row 必须只有一条，且 namespace 是 `receipt-index-receipt:`。
- source evidence 必须是两条、均 pass、digest 有效、路径存在。
- `allowed_use` 必须仍是 downstream lookup only。
- consumer boundary 和 model quality claim 必须仍是 bounded/governance 范围。
- blocked uses 必须保留生产提升、模型质量扩张和训练数据声明扩张三项。
- `promotion_ready` 和 `approved_for_promotion` 必须仍为 false。
- v990 的 `next_step` 必须指向 publish v990。

这些检查让 publication 不是简单复制 v990 review，而是重新确认所有会影响下游消费边界的字段。

## 输入输出流程

CLI 首先用 `locate_receipt_index_review_v991` 兼容目录输入和 JSON 输入。然后读取 v990 review JSON，调用 builder 生成 report，再通过 artifacts 模块写出五类产物。`--require-publication-ready` 和 `--require-lookup-ready` 会把失败检查转成非零退出码；`--require-promotion-ready` 在本版 expected failure，因为本版明确不允许 promotion。

本版真实运行命令为：

```powershell
python scripts/publish_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_v991.py e/990/解释/publication-receipt-index-receipt-index-review-v990 --out-dir e/991/解释/publication-receipt-index-receipt-index-publication-v991 --require-publication-ready --require-lookup-ready --force
```

输出显示 `status=pass`、`publication_ready=True`、`lookup_key_count=1`、`source_evidence_count=2`、`failed_check_count=0`、`passed_check_count=24`。

## 测试覆盖

聚焦测试覆盖五个场景：

- ready v990 review 能生成 ready publication。
- review status 被篡改为非 lookup-only 时失败。
- source receipt 路径丢失时失败。
- CLI 在 `--require-publication-ready` 下遇到篡改输入会返回 `1`，同时仍写出失败报告。
- JSON、CSV、TXT、Markdown、HTML 输出全部生成，文本和 HTML 中能看到 publication 语义。

这些断言保护的是发布边界和下游消费契约，而不是单纯检查字符串是否存在。

## 运行证据

运行证据写入 `e/991/解释/说明.md` 和 `e/991/解释/publication-receipt-index-receipt-index-publication-v991/`。HTML 报告通过 Playwright MCP 打开并截图到 `e/991/图片/`。截图证明本版 report 的浏览器视图可用，且页面展示了 publication ready、lookup key、source evidence、promotion=false 和检查表。

## 一句话总结

v991 把 v990 review 的只读许可落成可消费 publication，同时继续把生产提升和模型质量扩张挡在边界之外。

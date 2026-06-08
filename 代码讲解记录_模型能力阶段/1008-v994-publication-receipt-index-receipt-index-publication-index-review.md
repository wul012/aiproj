# v994 publication receipt index receipt index publication index review

本版目标是 review v993 生成的 publication index，确认它可以进入下一步 receipt 记录，但只能用于 downstream governance lookup。它解决的是一个细小但关键的边界问题：v993 已经把 v991 publication 与 v992 contract check 合并成 index，v994 再确认这个 index 没有丢失源证据、没有改变 lookup-only 语义，也没有把 `promotion_ready` 打开。

本版不训练模型，不改 checkpoint，不做新 benchmark，不把治理证据包装成模型质量提升结论。

## 前置路线

v991 把 v990 review 认可的 receipt index 发布为 lookup-only publication。v992 重新构建 v991 publication 并做 contract check。v993 把 v991/v992 合并成一条 `publication-index:` lookup row 和两条 source evidence。v994 的角色是在记录下游 receipt 之前做只读 review。

这条链路的价值不在于提升 LLM 输出能力，而在于保证模型能力阶段的证据消费是可追踪、可复核、可限界的。

## 关键文件

- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994.py`
  - v994 的核心 review builder。输入 v993 publication index，输出 review report。
- `src/minigpt/randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown 和 HTML，供运行归档与后续消费。
- `scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v994.py`
  - CLI 入口，支持 `--require-review-ready`、`--require-publication-ready` 和 `--require-promotion-ready`。
- `tests/test_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994.py`
  - 覆盖 ready index、坏 digest、lookup scope 篡改、CLI 失败码和输出写入。
- `src/minigpt/randomized_holdout_publication_constants.py`
  - 增加 v994 下一步常量，保持链路路由集中维护。
- `src/minigpt/__init__.py`
  - 暴露 v994 build/write 入口，避免包级 API 落后于脚本能力。

## 核心输入

输入可以是 v993 输出目录，也可以是 v993 JSON 文件。`locate_publication_index_v994()` 在目录模式下会定位：

```text
randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v993.json
```

`read_json_report()` 使用 `utf-8-sig` 读取 JSON，避免 BOM 或历史编码问题影响治理检查。

## 核心输出

`build_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_review_v994()` 输出一个 review report，主要字段包括：

- `status`
- `decision`
- `failed_count`
- `issues`
- `source_publication_index_summary`
- `source_publication_index`
- `publication_index_rows`
- `source_evidence_rows`
- `check_rows`
- `review`
- `summary`
- `interpretation`

其中 `review.review_status=approved_for_publication_index_receipt_lookup_only` 只代表可以继续记录 lookup-only receipt。它不等价于 production promotion，也不代表模型能力变好。

## 检查范围

v994 的 `_checks()` 保护以下边界：

- v993 publication index 文件必须存在。
- v993 `status` 和 `decision` 必须是 ready。
- summary 和 body 中的 index ready 字段必须一致。
- `lookup_scope` 与 `published_use` 必须保持 `downstream_governance_lookup_only`。
- `lookup_ready` 和 `contract_check_ready` 必须为真。
- 只能有一条 `publication-index:` row。
- source evidence 必须是两条，状态为 `pass`，且带 SHA-256。
- source publication、source check、source review、source receipt index 文件仍然存在。
- `consumer_boundary` 和 `model_quality_claim` 必须保持 bounded。
- `promotion_ready` 与 `approved_for_promotion` 必须继续为 False。
- v993 的 `failed_check_count` 必须为 0。
- v993 的 `next_step` 必须指向 v994 review。

这些检查让后续 receipt 不需要重新理解整条 v991-v993 链，只要消费 v994 review 即可确认 index 的使用边界。

## CLI 行为

脚本入口：

```powershell
python scripts/review_randomized_holdout_publication_receipt_packet_index_publication_receipt_index_receipt_index_publication_index_v994.py <publication-index-or-dir> --out-dir <dir> --require-review-ready --require-publication-ready --force
```

`--require-review-ready` 和 `--require-publication-ready` 都用于让 CI 或本地验证在 review 不满足条件时返回 1。`--require-promotion-ready` 也存在，但本版预期它返回 1，因为 v994 的设计目标正是阻断 promotion。

## 测试覆盖

测试不是只检查函数返回 pass，而是覆盖了会破坏治理边界的几类情况：

- ready v993 index 能生成 `review_ready=True` 的 v994 report。
- 将 source evidence 的 SHA-256 改成 `bad` 会触发 `source_evidence_digests`。
- 将 `lookup_scope` 篡改为 production promotion 后，CLI 在 `--require-review-ready` 下返回 1。
- 输出层能生成 JSON、CSV、TXT、Markdown、HTML。
- 目录定位函数能从 v993 输出目录找到标准 JSON 文件。

这让 v994 能真实保护 digest、lookup scope、no-promotion 和 CLI exit code。

## 运行证据

真实运行使用 `e/993/解释/publication-receipt-index-receipt-index-publication-index-v993` 作为输入，输出写入 `e/994/解释/publication-receipt-index-receipt-index-publication-index-review-v994/`。

本次结果为：

- `status=pass`
- `review_ready=True`
- `review_status=approved_for_publication_index_receipt_lookup_only`
- `publication_index_row_count=1`
- `source_evidence_count=2`
- `lookup_key_count=1`
- `contract_check_ready=True`
- `promotion_ready=False`
- `failed_check_count=0`
- `passed_check_count=24`

Playwright MCP 截图保存在 `e/994/图片/`，证明 HTML 报告可以打开，并能看到 Review Boundary 与 checks 表。

## 一句话总结

v994 把 v993 publication index 从“已构建”推进到“可被 receipt 消费”，同时继续把模型质量声明和生产 promotion 锁在边界外。

# v1124 publication receipt index review

## 本版目标与边界
v1124 的目标是 review v1123 receipt index。v1123 已经把 v1121 receipt 和 v1122 contract check 聚合成 lookup-only index；这一版在记录下一份 receipt 之前，对这份 index 做一次只读审查，确认索引行、source evidence、路径、lookup-only scope、contract-check ready 和 no-promotion 约束都没有漂移。

本版不训练模型，不改变 v1123 index，不创建生产发布许可，也不把 `review_ready=True` 当成模型能力增强。它只说明这份 index 可以被下一版 receipt 记录模块消费。

## 前置路线

```text
v1121 receipt
  -> v1122 contract check
  -> v1123 receipt index
  -> v1124 receipt index review
```

## 关键文件

```text
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1124.py
src/minigpt/randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1124_artifacts.py
scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1124.py
tests/test_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_review_v1124.py
```

主 builder 读取 v1123 index，抽取 `summary`、`receipt_index`、`receipt_index_rows` 和 `source_evidence_rows`，再构造 `review`、`summary`、`check_rows` 与 `interpretation`。artifact writer 把同一份 report 写成 JSON/CSV/TXT/Markdown/HTML。CLI 负责定位目录输入，并用 `--require-review-ready`、`--require-lookup-ready` 在失败时返回非零。

## 输入输出模型
输入是 `f/1123/解释/receipt-index-v1123` 中的 index JSON。关键输入字段包括：

- `summary.lookup_scope` 和 `summary.granted_use`：必须保持 downstream governance lookup only。
- `receipt_index_rows`：必须只有一条 lookup 行，并且 lookup key 使用 v1123 index namespace。
- `source_evidence_rows`：必须保留 receipt/check 两条上游证据和 digest。
- `receipt_index.receipt_path` / `receipt_index.receipt_check_path`：必须仍然指向存在的上游文件。
- `summary.next_step`：必须指向 v1123 review。

输出 report 的核心字段包括：

- `review.review_ready`：是否可以进入下一跳 receipt 记录。
- `review.review_status`：本版只读批准状态。
- `summary.lookup_ready` / `summary.contract_check_ready`：下游消费所需的两个关键 ready 位。
- `summary.promotion_ready=False`：明确继续阻止 promotion。
- `check_rows`：逐项审查结果，用于定位索引漂移。

## 核心检查
v1124 的 `_checks()` 保护以下事项：

- v1123 index 文件存在且 `status=pass`。
- v1123 decision 必须等于 v1123 ready decision。
- index summary 与 index body 都必须 ready。
- lookup scope 与 granted use 必须都是 downstream lookup only。
- contract check 必须 ready。
- lookup row 必须只有一条，lookup key 必须使用 v1123 namespace。
- source evidence 必须有两条、带 digest、状态为 pass。
- source receipt、receipt check、review 和 receipt index 路径都必须仍然存在。
- consumer boundary 与 model quality claim 仍然保持治理查阅边界。
- promotion 与 approved_for_promotion 必须继续为 false。
- source next step 必须从 v1123 index 指向 v1124 review。

## 运行证据
真实运行使用：

```text
python -B scripts/review_randomized_holdout_publication_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_receipt_index_v1124.py f/1123/解释/receipt-index-v1123 --out-dir f/1124/解释/receipt-index-review-v1124 --require-review-ready --require-lookup-ready --force
```

关键输出：

```text
status=pass
review_ready=True
receipt_index_row_count=1
lookup_key_count=1
source_evidence_count=2
lookup_ready=True
contract_check_ready=True
promotion_ready=False
passed_check_count=22
failed_check_count=0
```

Playwright MCP 截图保存为 `f/1124/图片/v1124-receipt-index-review.png`。页面展示 `Review Summary`、`Receipt Index Rows`、`Source Evidence` 和 `Checks`，说明 review 既保留索引结构，也保留上游证据和检查清单。

## 测试覆盖
focused tests 覆盖：

- 合法 v1123 index 可以生成 ready review。
- granted use 漂移到 production promotion 时失败。
- source evidence digest 缺失时失败。
- source receipt 路径漂移时失败。
- artifact writer 与 CLI 可以写出五种输出，并且目录定位函数可消费输出目录。

这些测试保护的是 receipt index review 的治理边界，不是模型质量本身。模型能力仍然只被描述为 `bounded_randomized_target_hidden_holdout_claim_only`。

## 链路角色
v1124 是本批次的收口 review。它把 v1123 index 从“可查索引”推进到“可记录 receipt 的已审查索引”，同时把 no-promotion 和 lookup-only 约束继续带到下一跳。后续如果继续推进，应进入 v1125 receipt 记录，而不是绕过 review 直接消费 index。

## 一句话总结
v1124 复核 v1123 receipt index，并把它限定为可记录、可查阅、不可 promotion 的 lookup-only 治理证据。

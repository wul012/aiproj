# v933 randomized holdout publication registry manifest review 代码讲解

## 本版目标和边界

v933 的目标是 review v932 生成的 registry manifest：

```text
v932 publication registry manifest
  -> v933 publication registry manifest review
```

它回答的问题是：

```text
这个 manifest 是否可以作为后续治理查询入口的只读输入？
```

回答是可以，但范围很窄：

```text
approved_for_governance_lookup_only
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不创建新模型质量结论。
- 不把 manifest review 当成发布批准。
- 不允许 `production_promotion`。

## 前置链路

v933 消费真实 v932 产物：

```text
e/932/解释/randomized-holdout-publication-registry-manifest
```

v932 已经证明 v931 packet 可以汇总为 manifest。v933 的职责不是重建 v932，而是复核 manifest 是否仍满足后续 lookup 的边界条件：

- manifest 本身 ready。
- entry count 与 entries 一致。
- entries 都是 registered。
- entries 都是 bounded accepted。
- entries 都没有 promotion。
- consumer boundary 仍为 `governance_lookup_only`。
- rejected use 明确为 `production_promotion`。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_manifest_review.py`

核心入口：

```python
build_randomized_holdout_publication_registry_manifest_review(...)
```

输入：

- `registry_manifest_report`：v932 manifest JSON。
- `registry_manifest_path`：manifest 文件路径。
- `title`：报告标题。
- `generated_at`：可选生成时间。

输出结构：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
registry_manifest_path
source_manifest_summary
source_manifest
entry_rows
check_rows
review
summary
interpretation
```

其中 `review` 是 v933 的核心结论：

```text
review_ready
review_id
review_status
registry_manifest_path
entry_count
reviewed_entry_ids
lookup_ready
bounded_publication_accepted
contract_check_ready
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
allowed_use
rejected_use
next_step
```

### `src/minigpt/randomized_holdout_publication_registry_manifest_review_artifacts.py`

负责输出：

- JSON：完整 review。
- CSV：entry 摘要。
- TXT：CI 日志友好的 key-value。
- Markdown：归档阅读。
- HTML：Playwright 截图和人工复核。

artifact writer 不做业务判断，只负责渲染 review report。

### `scripts/build_randomized_holdout_publication_registry_manifest_review.py`

CLI 用法：

```powershell
python scripts\build_randomized_holdout_publication_registry_manifest_review.py `
  --registry-manifest e\932\解释\randomized-holdout-publication-registry-manifest `
  --out-dir e\933\解释\randomized-holdout-publication-registry-manifest-review `
  --require-review-ready `
  --require-lookup-ready `
  --force
```

重要返回语义：

- `--require-review-ready`：review 不 ready 返回 1。
- `--require-lookup-ready`：lookup 不 ready 返回 1。
- `--require-promotion-ready`：当前应返回 1，因为 v933 明确不批准 promotion。

## 核心检查

v933 的检查点共 17 个：

```text
registry_manifest_file_exists
registry_manifest_passed
registry_manifest_decision_ready
manifest_summary_ready
manifest_scope_bounded
entry_count_positive
entries_registered
entries_bounded
entries_not_promoted
contract_check_ready
bounded_publication_accepted
consumer_boundary_governance
model_quality_claim_bounded
promotion_still_false
approved_for_promotion_false
source_checks_clean
source_next_step_matches
```

这些检查共同保护两个边界：

1. manifest 可以被 lookup 消费。
2. manifest review 不会滑成 promotion approval。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_manifest_review.py
```

覆盖场景：

- ready manifest 可以生成 lookup-only review。
- consumer boundary 被改成 `production_lookup` 时失败。
- entry 的 `promotion_ready` 被改成 true 时失败。
- artifact writer、locator、CLI、HTML/Markdown/TXT 渲染都接通。

聚焦测试：

```text
8 passed
```

## 真实运行证据

真实 v932 输入生成 v933 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_manifest_review_ready
review_status=approved_for_governance_lookup_only
lookup_ready=True
promotion_ready=False
rejected_use=production_promotion
passed_check_count=17
failed_check_count=0
```

证据目录：

```text
e/933/解释/randomized-holdout-publication-registry-manifest-review
e/933/图片/v933-randomized-holdout-publication-registry-manifest-review.png
```

## 链路角色

v933 处在 publication registry manifest 之后：

```text
registry packet
  -> registry manifest
  -> manifest review
  -> lookup packet
```

它是 lookup 前的一道边界确认，保证后续消费者拿到的是“可查询的 bounded evidence”，不是“可发布的生产模型批准”。

## 一句话总结

v933 把 v932 manifest 复核成 governance lookup only 的消费入口，并用测试和真实证据继续守住 production promotion=false。

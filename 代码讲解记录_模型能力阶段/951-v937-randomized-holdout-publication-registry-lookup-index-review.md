# v937 randomized holdout publication registry lookup index review 代码讲解

## 本版目标和边界

v937 的目标是 review v936 lookup index：

```text
v936 lookup index
  -> v937 lookup index review
```

它回答的问题是：

```text
lookup index 是否可以给 downstream governance lookup 消费？
```

回答是可以：

```text
approved_for_downstream_governance_lookup_only
```

明确不做：

- 不重新训练。
- 不重新 replay。
- 不扩展模型能力结论。
- 不批准 production promotion。

## 前置链路

v937 消费真实 v936 产物：

```text
e/936/解释/randomized-holdout-publication-registry-lookup-index
```

v936 已经把 v934 lookup packet 和 v935 contract check 合成一个 index。v937 负责确认这个 index 的下游消费边界：

- lookup scope 仍是 `governance_lookup_only`。
- lookup key 使用 `publication:` namespace。
- contract check ready。
- evidence count 至少包含 packet 和 check 两份证据。
- promotion 仍是 false。
- rejected use 仍是 `production_promotion`。

## 关键文件

### `src/minigpt/randomized_holdout_publication_registry_lookup_index_review.py`

核心入口：

```python
build_randomized_holdout_publication_registry_lookup_index_review(...)
```

输入：

- `lookup_index_report`：v936 index JSON。
- `lookup_index_path`：v936 index 路径。

输出结构：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
lookup_index_path
source_lookup_index_summary
source_lookup_index
entry_rows
check_rows
review
summary
interpretation
```

`review` 是本版核心：

```text
review_ready
review_id
review_status
lookup_index_path
entry_count
lookup_keys
downstream_ready
lookup_ready
contract_check_ready
promotion_ready
approved_for_promotion
consumer_boundary
model_quality_claim
allowed_use
rejected_use
next_step
```

### `src/minigpt/randomized_holdout_publication_registry_lookup_index_review_artifacts.py`

负责输出 JSON、CSV、TXT、Markdown 和 HTML。CSV 记录 entry rows，HTML 用于 Playwright 截图和人工核查。

### `scripts/build_randomized_holdout_publication_registry_lookup_index_review.py`

CLI 用法：

```powershell
python scripts\build_randomized_holdout_publication_registry_lookup_index_review.py `
  --lookup-index e\936\解释\randomized-holdout-publication-registry-lookup-index `
  --out-dir e\937\解释\randomized-holdout-publication-registry-lookup-index-review `
  --require-review-ready `
  --require-downstream-ready `
  --force
```

`--require-promotion-ready` 当前应返回 1，因为 v937 明确不批准 promotion。

## 核心检查

v937 的检查点共 16 个：

```text
lookup_index_file_exists
lookup_index_passed
lookup_index_decision_ready
lookup_index_summary_ready
lookup_scope_governance
lookup_ready
contract_check_ready
evidence_count
entries_present
lookup_keys_present
entries_not_promoted
consumer_boundary_governance
rejected_use_production_promotion
promotion_still_false
source_checks_clean
source_next_step_matches
```

这些检查保护 downstream 消费边界：

- index 必须 ready。
- lookup key 必须是 `publication:` namespace。
- contract check 必须 ready。
- production promotion 必须继续 rejected。

## 测试覆盖

新增测试文件：

```text
tests/test_randomized_holdout_publication_registry_lookup_index_review.py
```

覆盖场景：

- ready index 可以生成 downstream lookup-only review。
- lookup key namespace 错误时失败。
- contract check 不 ready 时失败。
- artifact writer、locator、CLI、TXT/Markdown/HTML 渲染接通。

聚焦测试：

```text
8 passed
```

## 真实运行证据

真实 v936 输入生成 v937 输出：

```text
status=pass
decision=randomized_holdout_publication_registry_lookup_index_review_ready
review_status=approved_for_downstream_governance_lookup_only
downstream_ready=True
lookup_ready=True
contract_check_ready=True
promotion_ready=False
rejected_use=production_promotion
passed_check_count=16
failed_check_count=0
```

证据目录：

```text
e/937/解释/randomized-holdout-publication-registry-lookup-index-review
e/937/图片/v937-randomized-holdout-publication-registry-lookup-index-review.png
```

## 链路角色

v937 位于 downstream guard 之前：

```text
lookup index
  -> lookup index review
  -> downstream guard
```

它把 lookup index 从“可消费 artifact”提升为“已复核的 downstream-only 输入”。

## 一句话总结

v937 把 v936 lookup index 复核为 downstream governance lookup only，并继续守住 production promotion=false。

# 第一百五十二篇代码讲解：第358版 governance stabilization reasons

## 本版目标和边界

v358 的目标是增强 v357 governance stabilization review 的解释能力。v357 已经决定短期暂停新增治理链，保留 7 条现有链；但如果只写 `keep/watch`，未来开发时仍然容易争论“为什么这条保留”“新需求该进哪条链”。

本版解决的问题是：每条治理链都必须写清楚 `review_reason` 和 `expansion_rule`。

本版不新增第 8 条治理链，不新增发布门禁，不改变训练、评估、release readiness 或 model card 的业务语义。

## 前置链路

```text
v357 governance stabilization review
  -> pause_new_governance_chains
  -> 7 chains, keep/watch/merge/cut

v358 governance stabilization reasons
  -> review_reason
  -> expansion_rule
  -> missing reason/rule becomes review
```

v358 的重点是让暂停期的裁剪标准可复核，而不是继续扩张 artifact 家族。

## 关键文件

### `src/minigpt/maintenance_policy.py`

`DEFAULT_GOVERNANCE_CHAINS` 的每条链新增：

```python
review_reason
expansion_rule
```

`review_reason` 解释为什么这条链应该保留或观察。例如：

- dataset provenance 会影响模型质量比较，所以是核心边界。
- benchmark history 是当前最接近模型能力变化的重复证据。
- training promotion 有价值，但重复 clean/review/block 字段的风险最高。

`expansion_rule` 解释未来新增需求应该如何并入。例如：

- dataset-only signal 优先并入 dataset provenance。
- 新 benchmark signal 只有影响 promotion/release review 时才扩展 benchmark history。
- narrative-only additions 应优先合入 maturity summary，而不是新开链。

`_governance_summary()` 新增：

- `missing_review_reason_count`
- `missing_expansion_rule_count`

如果链缺少 reason 或 rule，状态会变成 `review`，决策变成 `pause_and_review_governance_chains`。

### `src/minigpt/maintenance_policy_artifacts.py`

CSV、Markdown、HTML 都新增：

- `review_reason`
- `expansion_rule`

HTML 顶部 stat card 新增 `Missing rules`。表格从 5 列扩展到 7 列：

```text
Chain / Action / Consumer / Evidence / Review Reason / Expansion Rule / Next Action
```

这让人打开 HTML 就能看到：当前不是单纯暂停，而是在给未来扩展写边界。

### `scripts/check_maintenance_batching.py`

stdout 新增：

```text
governance_missing_review_reason_count=0
governance_missing_expansion_rule_count=0
```

这样命令行和 CI 日志也能检查稳定评审是否完整。

## 测试覆盖

`tests/test_maintenance_policy.py` 增强：

- 默认 7 条链必须 reason/rule 完整。
- 自定义薄弱链缺 reason/rule 时进入 `review`。
- Markdown 包含 `Expansion rule`。
- CLI stdout 包含 missing reason/rule 计数。

这些测试保护的是“治理链要有解释和扩展规则”，而不是只靠口头约束。

## 运行证据

运行证据放在：

```text
d/358/图片/01-governance-stabilization-reasons.png
d/358/解释/说明.md
```

截图显示：

- `Missing rules = 0`
- `Review Reason` 列
- `Expansion Rule` 列
- 7 条链的保留/观察理由和后续扩展边界

## 一句话总结

v358 把治理链暂停扩张的理由和扩展规则写进维护评审，让短期收口有可执行的判断标准。

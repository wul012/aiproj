# v717 pair-readiness route comparison

## 本版目标和边界

v717 的目标是把 v707、v712、v716 三次真实训练放进同一个比较报告。

本版不训练模型，也不修改 corpus。它只回答一个问题：

```text
structured-template route 是否比之前两条路线更接近 pair-full？
```

结论是：没有。v716 和 v707 的 default hit count 都是 1，只是命中的 term 从 `fixed` 换成了 `loss`。

## 前置链路

```text
v707 baseline split training -> hit fixed, miss loss
v712 loss-retention training -> miss fixed and loss
v716 structured-template training -> hit loss, miss fixed
v717 route comparison -> no pair-full, failure shape changed
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_route_comparison.py`
  - 三路比较 builder。
  - 读取三个 training run report。
  - 提取 checkpoint、pair-full、default hit count、hit terms、missed terms。

- `src/minigpt/model_capability_required_term_pair_readiness_route_comparison_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 用表格展示三条 route 的 hit/miss 差异。

- `scripts/run_model_capability_required_term_pair_readiness_route_comparison.py`
  - CLI。
  - 输入 `--baseline`、`--loss-retention`、`--structured-template`。

- `tests/test_model_capability_required_term_pair_readiness_route_comparison.py`
  - 覆盖 failure-shape change、checkpoint missing 阻断、pair-full candidate、输出格式。

## 核心数据结构

每条 route row 包含：

```text
label
status
decision
training_status
checkpoint_exists
pair_full_observed
default_continuation_hit_count
default_hit_terms
default_missed_terms
model_quality_claim
```

v717 不只比较 hit count，还比较 hit terms。这点重要，因为 v716 的 hit count 和 v707 一样，但实际命中的 term 不一样。

## 判定逻辑

核心 summary：

```text
structured_vs_baseline_default_hit_delta = structured_hit_count - baseline_hit_count
structured_vs_loss_retention_default_hit_delta = structured_hit_count - loss_retention_hit_count
failure_shape_changed = structured_hit_terms != baseline_hit_terms
```

真实结果：

```text
structured_vs_baseline_default_hit_delta=0
structured_vs_loss_retention_default_hit_delta=1
failure_shape_changed=True
```

因此 decision 是：

```text
pair_readiness_structured_template_changes_failure_shape_without_pair_full
```

这不是 promotion，也不是能力提升结论；它只是说明 structured-template 避开了 v712 的两边全坏，但没有超越 v707。

## 输出和证据

运行证据：

- `e/717/解释/model-capability-required-term-pair-readiness-route-comparison/`
- `e/717/图片/v717-pair-readiness-route-comparison.png`

关键表格：

```text
baseline-split: hit ['fixed'], miss ['loss']
loss-retention-prefix: hit [], miss ['fixed', 'loss']
structured-template: hit ['loss'], miss ['fixed']
```

## 测试覆盖

测试保护了三类行为：

- structured-template hit count 持平但 hit terms 翻转时，报告 failure-shape change。
- checkpoint 缺失会让 comparison fail。
- 如果某路线 pair-full，则 decision 会切到 candidate found。

这些断言避免将“失败形态变化”误判为“模型能力提升”。

## 一句话总结

v717 把三条真实 pair-readiness 路线放到同一张证据表里，确认 structured-template 只是改变失败形态，下一步应诊断 fixed recovery 或做容量对比。

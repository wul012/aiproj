# v308 training scale promotion index CI regression filtering

## 本版目标和边界

v308 的目标是把 v307 promotion report 中的 handoff batch CI regression 证据继续带入 promotion index，并影响 compare-input 过滤。

本版不修改 training execution，不新增 promoted comparison，不推进 seed 链路。它只修补 promotion index 的证据断点：promotion 已经知道 handoff batch 有 CI 回归，但 index 以前只看 `handoff_clean_batch_review_status` 是否为 `clean`。

## 前置路线

链路顺序是：

```text
training portfolio batch
-> training scale run
-> run comparison
-> run decision
-> workflow
-> handoff
-> promotion
-> promotion index
```

v308 只修改最后一层。

## 关键文件

- `src/minigpt/training_scale_promotion_index_helpers.py`
  - `_promotion_row()` 从 promotion summary / clean-batch guard 读取 `handoff_batch_maturity_ci_regression_count` 和 names。
  - `promoted_for_comparison` 判定新增 CI regression 条件：clean-required promotion 必须 status clean 且 CI regression count 为 0。
  - `_summary()` 统计 handoff CI regression 总数、selected 总数和名称集合。
  - `_recommendations()` 在 CI regression 存在时给出专门建议。

- `src/minigpt/training_scale_promotion_index.py`
  - CSV/Markdown/HTML 输出新增 handoff CI regression 字段。
  - Promotion table 增加 CI Regressions 列。

- `scripts/index_training_scale_promotions.py`
  - CLI stdout 新增 `handoff_batch_maturity_ci_regression_count` 和 `handoff_selected_batch_maturity_ci_regression_total`。

- `tests/test_training_scale_promotion_index.py`
  - fixture 新增 batch CI regression 字段。
  - 新增 clean-required + CI-regressed promotion 被排除出 compare inputs 的回归测试。

## 核心字段

index row 新增：

```text
handoff_batch_maturity_ci_regression_count
handoff_batch_maturity_ci_regression_names
handoff_selected_batch_maturity_ci_regression_count
```

index summary 新增：

```text
handoff_batch_maturity_ci_regression_count
handoff_selected_batch_maturity_ci_regression_total
handoff_batch_maturity_ci_regression_names
```

这些字段让 index 不只展示 promotion 是否 promoted，也能判断 promoted evidence 是否干净。

## 过滤规则

旧规则：

```text
promotion_status == promoted
and scale_run_exists
and (not clean_required or clean_status == clean)
```

v308 后：

```text
promotion_status == promoted
and scale_run_exists
and (
  not clean_required
  or (clean_status == clean and ci_regression_count == 0)
)
```

所以 clean-required 但 CI-regressed 的 promotion 会继续留在 index rows 中作为证据，但不会进入 `comparison_inputs`。

## 测试覆盖

新增测试验证：

- CI regression 字段能进入 row、summary、CSV、Markdown、HTML。
- clean-required promotion 在 `clean` 状态但 CI regression count 大于 0 时，不进入 compare inputs。
- CLI 输出包含 handoff CI regression count。
- 原有 clean/unclean batch-review 过滤仍然保持。

## 运行证据

运行截图与解释归档在：

```text
d/308/图片
d/308/解释/说明.md
```

## 一句话总结

v308 让 promotion index 不再只相信 clean 状态字符串，而能把 CI-regressed handoff batch 排除出 promoted compare inputs。

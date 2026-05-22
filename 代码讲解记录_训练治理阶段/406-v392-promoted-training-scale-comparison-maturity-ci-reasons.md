# v392 promoted training scale comparison maturity CI reasons 代码讲解

## 本版目标和边界

v392 的目标是把 v391 promotion index 已经聚合的 selected/global handoff maturity CI regression reason counts，继续带到 promoted training scale comparison。

promoted comparison 是从 promotion index 进入跨 promoted run 对比的入口。这个层会重新校验 clean-required handoff，过滤掉 stale 或 dirty 的 compare-ready 输入。v392 让这层不仅知道某个 promotion 因 CI regression 被排除，也能直接说明被排除的原因分布。

本版不改变 promoted comparison 的比较算法，不改变 clean-required CI-regressed promotion 的排除语义，不改变 baseline 选择规则，不改变 promoted decision、seed 或 seed handoff。它只把 reason counts 带到 comparison rows、summary、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 前置能力

本版承接 v384-v391：

```text
portfolio comparison maturity CI reasons
        |
        v
batch review reason counts
        |
        v
workflow + handoff
        |
        v
promotion summary
        |
        v
promotion index rows + summary
        |
        v
promoted comparison rows + summary
```

这条链路的意义是：当 promoted comparison 把 dirty clean-required 输入排除在比较之外时，报告能解释“为什么被排除”，而不是只留下 count。

## 关键文件

### `src/minigpt/promoted_training_scale_comparison.py`

`_clean_batch_review_guard()` 新增：

```text
handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
```

字段按优先级从 promotion index row、clean batch-review guard 和 summary 中读取。这样即便 index 标记 stale compare-ready，comparison 层也能重新校验并保留原因。

`_promotion_rows()` 将 reason counts 写入每个 promoted comparison row。

`_summary()` 新增四类聚合字段：

```text
handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts
```

前两类覆盖全部 promotion rows，后两类只覆盖最终仍进入 comparison 的 rows。

`_recommendations()` 在 CI-regressed evidence 可见但被排除时，会追加 observed reasons。并且当比较输入同时还有 selected batch blocker 等其他 review 信号时，也会额外补充 CI reason detail，避免原因被分支顺序遮住。

### `src/minigpt/promoted_training_scale_comparison_artifacts.py`

comparison CSV 新增行级 selected/global reason-count 字段。

Markdown summary 新增：

```text
Handoff batch CI regression reasons
Handoff selected batch CI regression reasons
Comparison-ready handoff batch CI regression reasons
Comparison-ready selected batch CI regression reasons
```

HTML stat cards 新增：

```text
Handoff CI reasons
Handoff selected CI reasons
Ready CI reasons
Ready selected CI reasons
```

这些输出用于人读审查；机器消费仍优先读取 `promoted_training_scale_comparison.json`。

### `scripts/compare_promoted_training_scale_runs.py`

stdout 新增：

```text
handoff_batch_maturity_ci_regression_reason_counts=<json>
handoff_selected_batch_maturity_ci_regression_reason_counts=<json>
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts=<json>
comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts=<json>
```

这样终端和 CI 日志可以区分“全量 promotion 风险”和“实际进入比较的风险”。

### `tests/test_promoted_training_scale_comparison.py`

测试 fixture 新增：

```text
batch_ci_regression_reason_counts
selected_batch_ci_regression_reason_counts
```

定向测试断言：

- dirty clean-required CI-regressed promotion row 保留 selected/global reason counts；
- full summary 聚合 reason counts；
- comparison-ready summary 对被排除的 dirty row 保持空 reason counts；
- CSV、Markdown、HTML 和 CLI stdout 展示 reason counts；
- stale compare-ready 输入仍被 comparison 层重新阻断，并带上 observed reason detail。

## 数据结构说明

promotion row 示例：

```json
{
  "handoff_batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1,
    "workflow-order-regressed": 1
  },
  "handoff_selected_batch_maturity_ci_regression_reason_counts": {
    "workflow-order-regressed": 1
  }
}
```

promoted comparison summary 示例：

```json
{
  "handoff_batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1,
    "workflow-order-regressed": 1
  },
  "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": {}
}
```

这表示 CI-regressed promotion 仍保留在报告里，但没有进入 comparison-ready 输入集合。

## 运行流程

```text
build_promoted_training_scale_comparison()
        |
        v
load_training_scale_promotion_index()
        |
        v
_promotion_rows()
  - read reason counts from index rows
  - re-check clean-required CI regressions
        |
        v
_comparison_inputs()
  - compare only clean promoted inputs
        |
        v
_summary()
  - aggregate full and comparison-ready reason counts
        |
        v
write JSON / CSV / Markdown / HTML
        |
        v
scripts/compare_promoted_training_scale_runs.py
  - print full and comparison-ready reason-count JSON
```

promoted comparison 继续只做 promoted run 对比，不执行训练、不生成新的 promotion，也不改变上游 promotion index。

## 测试覆盖

本版定向测试：

```text
python -m pytest tests/test_promoted_training_scale_comparison.py -q
```

覆盖点：

- 只比较 promoted inputs；
- mixed suite 仍进入 summary 和 recommendations；
- suite guard、batch review context、clean batch-review guard 原有语义保持；
- clean-required dirty input 仍被过滤；
- clean-required CI-regressed input 仍被过滤并解释 reason counts；
- stale compare-ready CI-regressed input 会被 comparison 层重新阻断；
- row、summary、CSV、Markdown、HTML、CLI stdout 都带 reason counts。

## 证据归档

本版运行截图和说明放在：

```text
d/392/图片
d/392/解释/说明.md
```

`d/392/解释/v392-promoted-training-scale-comparison-maturity-ci-reasons-evidence.html` 是静态证据页，用于 Playwright MCP 截图；它不是最终机器消费源。

## 一句话总结

v392 把 maturity CI regression reason counts 从 promotion index 推进到 promoted comparison，让跨 promoted run 比较报告也能解释被排除的 CI 回归原因。

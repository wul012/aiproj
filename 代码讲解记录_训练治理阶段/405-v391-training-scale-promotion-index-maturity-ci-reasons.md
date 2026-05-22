# v391 training scale promotion index maturity CI reasons 代码讲解

## 本版目标和边界

v391 的目标是把 v390 training scale promotion 已经携带的 selected/global handoff maturity CI regression reason counts，继续带到 promotion index。

promotion index 是多份 promotion 报告进入后续 promoted comparison 前的汇总层。如果这里只保留 CI regression count 和 names，reviewer 可以知道有风险，却看不到风险原因。v391 补齐这段多 promotion 汇总证据链。

本版不改变 promotion index 的 compare input 筛选规则，不改变 clean-required CI-regressed promotion 的排除语义，不改变 promoted comparison、promoted decision 或 seed handoff。它只把 reason counts 带到 index row、summary、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 前置能力

本版承接 v384-v390：

```text
portfolio comparison maturity CI reasons
        |
        v
batch review reason counts
        |
        v
scale-run decision
        |
        v
workflow + handoff
        |
        v
promotion summary
        |
        v
promotion index rows + summary
```

这条链路的意义是：当多份 promotion 汇总到一个 index 时，index 不只知道哪些 promotion 有 CI 回归，还能知道它们为什么回归。

## 关键文件

### `src/minigpt/training_scale_promotion_index_helpers.py`

`_promotion_row()` 新增：

```text
handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
```

行级字段来自 promotion summary 和 clean batch-review guard。

`_summary()` 新增聚合字段：

```text
handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
```

聚合逻辑使用 `_sum_reason_counts()`，对所有 promotion row 的 reason-count map 做同名原因求和。

`_recommendations()` 在存在 handoff batch CI regression 时，会追加 observed reasons，例如：

```text
Observed reasons: missing-ci-step:1, workflow-order-regressed:1.
```

### `src/minigpt/training_scale_promotion_index.py`

index CSV 新增行级 selected/global reason-count 字段。

Markdown summary 新增：

```text
Handoff batch CI regression reasons
Handoff selected batch CI regression reasons
```

HTML stat cards 新增：

```text
Handoff CI reasons
Selected CI reasons
```

这些输出用于人读审查；机器消费仍优先读取 `training_scale_promotion_index.json`。

### `scripts/index_training_scale_promotions.py`

stdout 新增：

```text
handoff_batch_maturity_ci_regression_reason_counts=<json>
handoff_selected_batch_maturity_ci_regression_reason_counts=<json>
```

这样 CI 日志或终端读者可以直接看到 index 层聚合后的 reason-count 证据。

### `tests/test_training_scale_promotion_index.py`

测试 fixture 新增：

```text
batch_ci_regression_reason_counts
selected_batch_ci_regression_reason_counts
```

定向测试断言：

- promotion row 保存 selected/global reason counts；
- index summary 聚合 selected/global reason counts；
- CSV、Markdown、HTML 展示 reason counts；
- CLI stdout 打印聚合 reason-count JSON；
- clean-required CI-regressed promotion 仍被排除出 compare inputs。

## 数据结构说明

promotion row 示例：

```json
{
  "handoff_selected_batch_maturity_ci_regression_reason_counts": {
    "workflow-order-regressed": 1
  },
  "handoff_batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1,
    "workflow-order-regressed": 1
  }
}
```

index summary 示例：

```json
{
  "handoff_selected_batch_maturity_ci_regression_reason_counts": {
    "workflow-order-regressed": 1
  },
  "handoff_batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1,
    "workflow-order-regressed": 1
  }
}
```

summary 字段是所有 promotion rows 的聚合结果。它用于多 promotion 审查，不替代各个 promotion 的原始 JSON。

## 运行流程

```text
build_training_scale_promotion_index()
        |
        v
load_training_scale_promotion()
        |
        v
_promotion_row()
  - copy selected/global reason counts from promotion summary
        |
        v
_summary()
  - aggregate reason counts across rows
        |
        v
_comparison_inputs()
  - unchanged compare-input selection
        |
        v
write JSON / CSV / Markdown / HTML
        |
        v
scripts/index_training_scale_promotions.py
  - print reason-count JSON to stdout
```

promotion index 继续只做汇总和 compare input 组织，不执行训练、不重跑 benchmark，也不改变 promoted comparison 行为。

## 测试覆盖

本版定向测试：

```text
python -m pytest tests/test_training_scale_promotion_index.py -q
```

覆盖点：

- promoted reports 仍能生成 compare inputs；
- review/blocked reports 仍不进入 compare inputs；
- baseline 仍必须来自可比较 promotion；
- suite guard、batch review context、clean batch-review guard 原有语义保持；
- clean-required CI-regressed promotion 仍从 compare inputs 排除；
- row、summary、CSV、Markdown、HTML、CLI stdout 都带 reason counts；
- helper module 仍驱动 comparison input 和 summary 聚合。

## 证据归档

本版运行截图和说明放在：

```text
d/391/图片
d/391/解释/说明.md
```

`d/391/解释/v391-training-scale-promotion-index-maturity-ci-reasons-evidence.html` 是静态证据页，用于 Playwright MCP 截图；它不是最终机器消费源。

## 一句话总结

v391 把 maturity CI regression reason counts 从 promotion 推进到 promotion index，让多 promotion 汇总报告也能解释 handoff CI 回归原因。

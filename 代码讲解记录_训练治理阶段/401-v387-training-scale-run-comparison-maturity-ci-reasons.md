# v387 training scale run comparison maturity CI reasons 代码讲解

## 本版目标和边界

v387 的目标是把 v386 gated training scale run 已经保存的 batch maturity CI regression reason counts，继续带到 training scale run comparison。

v386 让单个 scale-run 报告能说明 batch CI 回归原因。但多 run comparison 层原先只聚合 `batch_maturity_ci_regression_count` 和 `batch_maturity_ci_regression_names`，所以跨 run 评审仍然看不到原因构成。v387 补齐 multi-run readiness review 的原因计数视图。

本版不改变 readiness 评分，不改变 baseline 选择，不改变 decision/handoff/promotion。它只在 scale-run comparison 的 run row、summary、CSV、Markdown、HTML 和 CLI summary 中保留原因计数。

## 前置能力

本版承接 v386：

```text
training_scale_run.batch_summary.maturity_ci_regression_reason_counts
        |
        v
training_scale_run_comparison.runs[].batch_maturity_ci_regression_reason_counts
        |
        v
training_scale_run_comparison.summary.batch_maturity_ci_regression_reason_counts
        |
        v
CSV / Markdown / HTML / scripts/compare_training_scale_runs.py stdout
```

这条链路的意义是：单个 scale-run 保存 batch 原因，多 run comparison 聚合这些原因，帮助 reviewer 判断多个 scale-run 的 CI 风险是否来自同一类问题。

## 关键文件

### `src/minigpt/training_scale_run_comparison.py`

`_run_summary()` 新增：

```text
batch_maturity_ci_regression_reason_counts
```

字段来自 `training_scale_run.json` 的：

```text
batch_summary.maturity_ci_regression_reason_counts
```

`_comparison_summary()` 新增同名聚合字段：

```text
batch_maturity_ci_regression_reason_counts
```

它用 `_merge_reason_counts()` 合并所有 run row 的原因计数。`_int_mapping()` 会丢弃空 key、非正数 count 和非 dict 输入，保持 summary 稳定。

### `src/minigpt/training_scale_run_comparison_artifacts.py`

CSV 新增：

```text
batch_maturity_ci_regression_reason_counts
```

Markdown summary 新增：

```text
Batch CI regression reasons
```

Runs 表新增 `CI Reasons` 列。HTML stat cards 和 Runs 表也展示原因计数。这里的渲染产物是人读证据；下游机器消费仍应读取 JSON。

### `tests/test_training_scale_run_comparison.py`

`test_comparison_carries_batch_ci_regression_context_into_outputs()` 扩展了 fixture：

```json
{
  "maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 2,
    "ci_order_violations_increased": 1
  }
}
```

测试断言：

- run row 保留 `batch_maturity_ci_regression_reason_counts`；
- comparison summary 聚合 reason counts；
- CSV 输出包含新列和值；
- Markdown/HTML 展示 `ci_failed_checks_increased:2`。

### `scripts/compare_training_scale_runs.py`

脚本已经打印：

```text
summary=<json>
```

因为 v387 把聚合原因放进 summary，CLI stdout 自动携带新字段，不需要新增参数。

## 数据结构说明

输入来自单个 scale-run：

```json
{
  "batch_summary": {
    "maturity_ci_regression_reason_counts": {
      "ci_failed_checks_increased": 2
    }
  }
}
```

comparison row 中变为：

```json
{
  "batch_maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 2
  }
}
```

comparison summary 聚合后：

```json
{
  "batch_maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 2
  }
}
```

字段使用 `batch_maturity_` 前缀，是为了说明它仍是 batch maturity review 的证据，而不是 comparison 自己重新分类出来的原因。

## 运行流程

```text
build_training_scale_run_comparison()
        |
        v
_run_summary()
  - read each run's batch_summary reason counts
        |
        v
_comparison_summary()
  - aggregate reason counts across runs
        |
        v
write_training_scale_run_comparison_outputs()
  - JSON / CSV / Markdown / HTML
        |
        v
scripts/compare_training_scale_runs.py stdout summary
```

这条流程让多 run readiness comparison 不只比较“谁有 CI 回归”，还可以解释这些回归由哪些原因构成。

## 测试覆盖

本版定向测试运行：

```text
python -m pytest tests/test_training_scale_run_comparison.py -q
```

测试覆盖了 allowed/blocked runs、suite mismatch、artifact facade、一条带 CI reason counts 的手工 run summary、CSV、Markdown、HTML。

## 证据归档

本版运行截图和说明放在：

```text
d/387/图片
d/387/解释/说明.md
```

`d/387/解释/v387-training-scale-run-comparison-maturity-ci-reasons-evidence.html` 是本版静态证据页，用于 Playwright 截图和文档验证；它不是最终机器消费源。

## 一句话总结

v387 把 maturity CI regression reason counts 从单个 gated scale run 推进到 multi-run comparison，使跨 run readiness review 也能看到 CI 回归原因构成。

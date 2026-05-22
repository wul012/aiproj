# v388 training scale run decision maturity CI reasons 代码讲解

## 本版目标和边界

v388 的目标是把 v387 training scale run comparison 已经聚合好的 batch maturity CI regression reason counts，继续带到 training scale run decision。

前几版已经形成一条清晰链路：portfolio comparison 识别 CI 原因，batch 保留原因，gated scale run 保留原因，scale-run comparison 聚合原因。v388 补上 decision 层，让“下一步是否执行哪个 run”的报告也能看到这些原因。

本版不改变候选 run 选择算法，不改变 readiness 分数，不改变 clean batch-review gate 的判定条件，也不推进 handoff/promotion。它只把 reason counts 作为解释性证据带进 decision summary、CSV、Markdown、HTML 和 CLI stdout。

同时，本版把重复出现的 reason-count 解析和展示 helper 收到 `report_utils.py`，避免后续每个模块再各写一份 `_int_mapping()` / `_fmt_mapping()`。

## 前置能力

本版承接 v384-v387：

```text
training_portfolio_comparison.summary.maturity_ci_regression_reason_counts
        |
        v
training_portfolio_batch.comparison_review_summary.maturity_ci_regression_reason_counts
        |
        v
training_scale_run.batch_summary.maturity_ci_regression_reason_counts
        |
        v
training_scale_run_comparison.summary.batch_maturity_ci_regression_reason_counts
        |
        v
training_scale_run_decision.summary.batch_maturity_ci_regression_reason_counts
```

这条链路的意义是：到 decision 层时，reviewer 不只知道 selected run 或 comparison 有 CI 回归，还能看到回归原因构成，比如 failed checks 变多还是 workflow order violation 变多。

## 关键文件

### `src/minigpt/report_utils.py`

新增两个共享 helper：

```text
positive_int_mapping(value)
format_mapping(value)
```

`positive_int_mapping()` 负责把 dict 里的 key 清理成非空字符串，并只保留正整数 count。`format_mapping()` 把映射渲染为 `reason:count` 形式，用在 Markdown/HTML 人读证据里。

这两个 helper 替代了多个模块中重复的 `_int_mapping()` / `_fmt_mapping()` 逻辑。

### `src/minigpt/training_scale_run_decision.py`

rejected run row 新增：

```text
batch_maturity_ci_regression_reason_counts
```

decision summary 新增两个字段：

```text
selected_batch_maturity_ci_regression_reason_counts
batch_maturity_ci_regression_reason_counts
```

第一个来自被选中的 run row，第二个来自 comparison summary 的聚合字段。字段命名故意区分 selected 和 aggregate，避免把“选中 run 的原因”与“整个 comparison 的原因”混在一起。

### `src/minigpt/training_scale_run_decision_artifacts.py`

CSV 新增 selected/global 两个 reason-count 字段。

Markdown 新增：

```text
Selected batch CI regression reasons
Batch CI regression reasons
```

HTML stat cards 新增：

```text
Selected CI reasons
CI regression reasons
```

这些渲染产物是 human review evidence；机器消费仍应读取 `training_scale_run_decision.json`。

### `scripts/decide_training_scale_run.py`

stdout 新增：

```text
batch_maturity_ci_regression_reason_counts=<json>
selected_batch_maturity_ci_regression_reason_counts=<json>
```

这样 CI 日志和终端读者不打开 JSON 也能看到 reason-count 证据。

### reason-count helper 迁移

以下模块改为复用 `report_utils`：

```text
training_portfolio_batch.py
training_portfolio_comparison.py
training_portfolio_comparison_review.py
training_scale_run.py
training_scale_run_comparison.py
training_scale_run_comparison_artifacts.py
```

这是本版的维护收束部分。它不改变外部 schema，只把重复解析/展示逻辑收为一个公共实现。

## 数据结构说明

comparison 输入：

```json
{
  "summary": {
    "batch_maturity_ci_regression_reason_counts": {
      "ci_failed_checks_increased": 2,
      "ci_order_violations_increased": 1
    }
  }
}
```

decision 输出：

```json
{
  "summary": {
    "selected_batch_maturity_ci_regression_reason_counts": {
      "ci_failed_checks_increased": 2,
      "ci_order_violations_increased": 1
    },
    "batch_maturity_ci_regression_reason_counts": {
      "ci_failed_checks_increased": 2,
      "ci_order_violations_increased": 1
    }
  }
}
```

当没有 selected run 时，selected reason counts 为 `{}`。当 comparison 没有原因字段时，aggregate reason counts 也保持 `{}`，兼容旧报告。

## 运行流程

```text
build_training_scale_run_decision()
        |
        v
load training_scale_run_comparison.json
        |
        v
copy selected run reason counts into selected summary
        |
        v
copy comparison summary reason counts into decision summary
        |
        v
write JSON / CSV / Markdown / HTML
        |
        v
scripts/decide_training_scale_run.py prints selected/global reason-count JSON
```

这个流程保证 decision 层仍然只做“选择下一步执行对象”的职责，CI reason 分类仍来自上游 maturity/portfolio comparison 证据。

## 测试覆盖

本版新增和扩展的测试覆盖：

- `tests/test_report_utils.py`：验证 `positive_int_mapping()` 会过滤空 key、零值、坏数字，并稳定排序；验证 `format_mapping()` 的人读输出。
- `tests/test_training_scale_run_decision.py`：验证 selected/global reason counts 进入 decision summary；验证 CSV、Markdown、HTML、CLI stdout 都能看到 `ci_failed_checks_increased`。
- portfolio batch/comparison/review 与 scale-run comparison 的定向测试一起运行，确认 helper 迁移没有改变原有语义。

## 证据归档

本版运行截图和说明放在：

```text
d/388/图片
d/388/解释/说明.md
```

`d/388/解释/v388-training-scale-run-decision-maturity-ci-reasons-evidence.html` 是静态证据页，用于 Playwright MCP 打开和截图；它不是机器消费源。

## 一句话总结

v388 把 maturity CI regression reason counts 推进到 training scale run decision，并把重复 reason-count helper 收束到共享工具层，让训练治理链路更完整也更容易维护。

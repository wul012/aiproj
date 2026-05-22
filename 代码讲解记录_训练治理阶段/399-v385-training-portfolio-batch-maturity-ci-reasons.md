# v385 training portfolio batch maturity CI reasons 代码讲解

## 本版目标和边界

v385 的目标是把 v384 training portfolio comparison 已经汇总好的 maturity CI regression reason counts，继续带到 training portfolio batch 的 comparison review summary。

v384 解决的是“单次 portfolio comparison 能看见原因计数”。但 batch 层在汇总多个 variant 的 comparison review 时，仍然只保留 `maturity_ci_regression_count` 和 `maturity_ci_regression_names`。这会让 batch HTML/Markdown 和 CLI 输出只能看到“哪些 variant 被 CI 规则卡住”，看不到“为什么卡住”。v385 补齐这个 batch 级别的证据视图。

本版不改变 batch plan 的生成方式，不改变 variant 执行流程，不改变 comparison 是否写出，也不改变 batch 的 baseline 选择。它只在 batch review summary 和 batch rendered outputs 上保留来自 comparison 的原因计数。

## 前置能力

本版承接 v384：

```text
training portfolio comparison.summary.maturity_ci_regression_reason_counts
        |
        v
training portfolio batch.comparison_review_summary
        |
        v
batch markdown / HTML / CLI stdout
```

这条链路的意义是：单次比较先确定 CI 回归原因，batch 层再把这些原因和被阻断的 variant 一起展示出来，方便选择下一轮基线或判断是否需要重跑。

## 关键文件

### `src/minigpt/training_portfolio_batch.py`

`_comparison_review_summary()` 新增：

```text
maturity_ci_regression_reason_counts
```

它从 nested comparison summary 读取 `maturity_ci_regression_reason_counts`，并用 `_int_mapping()` 做一次规范化，保证输出只保留有效的正整数 reason counts。

这个字段和现有的：

```text
maturity_ci_regression_count
maturity_ci_regression_names
```

一起构成 batch comparison review summary 的 CI 证据层。前者说明数量，后两者说明有哪些 variant，以及这些 variant 的原因构成。

### `src/minigpt/training_portfolio_batch_artifacts.py`

Markdown 和 HTML 现在显示：

```text
CI regression reasons
```

并把它放在 comparison 摘要和 comparison 面板里。这样 batch 读者不用再打开单次 comparison JSON，就能直接在 batch report 里看见原因计数。

### `tests/test_training_portfolio_batch.py`

测试 fixture 现在直接构造带有 `maturity_ci_regression_reason_counts` 的 comparison report，并断言：

- review summary 会保留 reason counts；
- Markdown 会显示 reason counts；
- HTML 会显示 reason counts；
- batch 运行时的 review summary 路径仍然正常。

这个测试关注的是 batch 汇总链路，不是再重复单次 comparison 的字段测试。

### `scripts/run_training_portfolio_batch.py`

CLI 仍然只打印 `comparison_review_summary` 的 JSON，但因为 summary 里已经包含 reason counts，所以 stdout 能把这个字段一起带出去。脚本本身不需要再新增参数或分支。

## 数据结构说明

batch comparison review summary 现在包含：

```json
{
  "maturity_ci_regression_count": 1,
  "maturity_ci_regression_names": ["candidate"],
  "maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 2,
    "ci_order_violations_increased": 1
  }
}
```

这里的 reason counts 是从单次 comparison 汇总而来，不是 batch 自己重新计算出来的。batch 的职责只是保留和展示。

## 运行流程

```text
run_training_portfolio_batch_plan()
        |
        v
run_training_portfolio_plan() per variant
        |
        v
build_training_portfolio_comparison()
        |
        v
_comparison_review_summary()
        |
        v
batch markdown / HTML / CLI stdout
```

这条流程让 batch 层从“有 CI 阻断”推进到“batch 里能直接看到阻断原因是什么”。

## 测试覆盖

本版定向测试运行：

```text
python -m pytest tests/test_training_portfolio_batch.py -q
```

测试覆盖了 reason-count carryover 和 rendered output 语义，而不是只检查字段名是否存在。

后续全量测试、编码检查和截图会在收口时一起跑，防止 batch 汇总改动影响其他训练链路。

## 证据归档

本版运行截图和说明放在：

```text
d/385/图片
d/385/解释/说明.md
```

`d/385/解释/v385-training-portfolio-batch-maturity-ci-reasons-evidence.html` 是本版静态证据页，用于 Playwright 截图和文档验证；它不是最终机器消费源。

## 一句话总结

v385 把 maturity CI regression reason counts 从单次 portfolio comparison 推进到 batch review summary，使 batch 级别的 variant 选择也能看到回归原因。

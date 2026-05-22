# v389 workflow handoff maturity CI reasons 代码讲解

## 本版目标和边界

v389 的目标是把 v388 training scale run decision 已经保留的 selected/global batch maturity CI regression reason counts，继续带到 workflow 和 handoff。

v388 让 decision 层能解释“为什么这个 comparison 有 CI 回归”。但 workflow 和 handoff 是更接近执行前审查的位置，如果这两层只显示 CI 回归数量和名字，reviewer 仍然需要回到 decision JSON 才知道具体原因。v389 补齐这段执行前证据链。

本版不改变 workflow 的 profile 执行流程，不改变 decision 选择算法，不改变 handoff 执行命令，不改变 clean batch-review gate 的阻断语义。它只把上游 reason counts 作为解释性证据带到 workflow summary、handoff guard/summary、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 前置能力

本版承接 v384-v388：

```text
portfolio comparison maturity CI reasons
        |
        v
batch review reason counts
        |
        v
gated scale-run batch_summary
        |
        v
scale-run comparison summary
        |
        v
scale-run decision summary
        |
        v
workflow summary + handoff summary
```

这条链路的意义是：当用户准备执行 handoff command 时，当前报告已经能说明 CI 回归原因，而不是只说“有 CI regression”。

## 关键文件

### `src/minigpt/training_scale_workflow.py`

`_workflow_summary()` 新增：

```text
selected_batch_maturity_ci_regression_reason_counts
batch_maturity_ci_regression_reason_counts
```

字段直接来自 decision summary。`_workflow_recommendations()` 在存在 aggregate reason counts 时，会把 `reason:count` 追加进建议文本。

### `src/minigpt/training_scale_workflow_artifacts.py`

workflow CSV 新增 selected/global reason-count 字段。

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

这些输出用于人读审查；机器消费仍优先读取 `training_scale_workflow.json`。

### `scripts/run_training_scale_workflow.py`

stdout 新增：

```text
batch_maturity_ci_regression_reason_counts=<json>
selected_batch_maturity_ci_regression_reason_counts=<json>
```

这样 CI 日志或终端读者可以直接看到 workflow 层 reason-count 证据。

### `src/minigpt/training_scale_handoff.py`

`_clean_batch_review_guard()` 新增 selected/global reason-count 字段，并使用 decision summary 优先、workflow summary 兜底。

`_summary()` 新增同名字段，handoff summary 因此可以在执行前保留完整 CI reason context。

`_recommendations()` 在发现 batch maturity CI regression 时，把观察到的 reason counts 写入建议，例如：

```text
Observed reasons: ci_failed_checks_increased:2, ci_order_violations_increased:1.
```

### `src/minigpt/training_scale_handoff_artifacts.py`

handoff CSV、Markdown、HTML 展示 selected/global reason counts，让执行交接报告不用回查 decision JSON 也能解释 CI 风险。

## 数据结构说明

workflow summary 示例：

```json
{
  "selected_batch_maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 2
  },
  "batch_maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 3,
    "ci_order_violations_increased": 1
  }
}
```

handoff summary 保持同样字段：

```json
{
  "selected_batch_maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 2
  },
  "batch_maturity_ci_regression_reason_counts": {
    "ci_failed_checks_increased": 3,
    "ci_order_violations_increased": 1
  }
}
```

selected 字段表示当前被选中执行候选的原因，aggregate 字段表示整个 comparison/workflow 范围内的原因。

## 运行流程

```text
run_training_scale_workflow()
        |
        v
build_training_scale_run_decision()
        |
        v
_workflow_summary()
  - copy selected/global reason counts
        |
        v
write workflow JSON / CSV / Markdown / HTML
        |
        v
build_training_scale_handoff()
        |
        v
_clean_batch_review_guard() and _summary()
  - read decision reason counts, fallback to workflow reason counts
        |
        v
write handoff JSON / CSV / Markdown / HTML
```

handoff 层继续只做执行交接和验证，不重新分类 CI 原因。

## 测试覆盖

本版定向测试：

```text
python -m pytest tests/test_training_scale_workflow.py tests/test_training_scale_handoff.py -q
```

覆盖点：

- workflow summary 保存 selected/global reason counts；
- workflow CSV、Markdown、HTML 展示 reason counts；
- workflow CLI stdout 打印 selected/global reason-count JSON；
- handoff summary 保存 selected/global reason counts；
- handoff CSV、Markdown、HTML 展示 reason counts；
- handoff recommendations 带上具体 reason-count detail；
- strict clean-batch gate 的原有阻断语义保持不变。

## 证据归档

本版运行截图和说明放在：

```text
d/389/图片
d/389/解释/说明.md
```

`d/389/解释/v389-workflow-handoff-maturity-ci-reasons-evidence.html` 是静态证据页，用于 Playwright MCP 截图；它不是最终机器消费源。

## 一句话总结

v389 把 maturity CI regression reason counts 从执行决策推进到 workflow 和 handoff，让真正执行前的审查报告也能解释 CI 回归原因。

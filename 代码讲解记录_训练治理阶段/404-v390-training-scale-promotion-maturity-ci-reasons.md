# v390 training scale promotion maturity CI reasons 代码讲解

## 本版目标和边界

v390 的目标是把 v389 workflow/handoff 已经携带的 selected/global maturity CI regression reason counts，继续带到 training scale promotion。

promotion 是把一次 handoff 视为“可晋升训练证据”的审查入口。如果这里仍然只显示 CI regression count 和 regressed names，reviewer 需要回查 handoff 或 decision 才能知道具体原因。v390 补齐这段 promotion 证据链，让晋升报告直接说明 CI 回归原因。

本版不改变 promotion 的 ready/review/blocked 判定，不改变 clean batch-review requirement 的阻断语义，不改变 promotion index、promoted comparison、promoted decision 或 seed handoff。它只把 handoff reason counts 作为解释性证据带入 promotion summary、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 前置能力

本版承接 v384-v389：

```text
portfolio comparison maturity CI reasons
        |
        v
batch review reason counts
        |
        v
gated scale-run summary
        |
        v
scale-run comparison summary
        |
        v
scale-run decision summary
        |
        v
workflow + handoff summary
        |
        v
training scale promotion summary
```

这条链路的意义是：当一次 handoff 被拿来做 promotion review 时，当前 promotion 报告已经能解释 CI 回归原因，而不是只留下一个数量。

## 关键文件

### `src/minigpt/training_scale_promotion.py`

`_suite_guard()` 新增：

```text
handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
```

字段来自 handoff summary，保留 selected 和 aggregate 两个视角。

`_clean_batch_review_guard()` 也读取同名 reason counts，并作为 strict clean-batch requirement 的兜底来源。这样 clean-required handoff 因 CI regression 被挡住时，promotion recommendation 可以说明挡住的原因。

`_summary()` 将 reason counts 写入 promotion summary：

```text
handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
```

`_recommendations()` 在 CI-regressed handoff batch evidence 或 clean batch-review requirement 未满足时追加 observed reasons，例如：

```text
Observed reasons: missing-ci-step:1, workflow-order-regressed:1.
```

### `src/minigpt/training_scale_promotion_artifacts.py`

promotion CSV 新增 selected/global reason-count 字段。

Markdown 新增：

```text
Handoff selected batch CI regression reasons
Handoff batch CI regression reasons
```

HTML stat cards 新增：

```text
Selected CI reasons
Batch CI reasons
```

这些渲染输出用于人读审查；机器消费仍优先读取 `training_scale_promotion.json`。

### `scripts/build_training_scale_promotion.py`

stdout 新增：

```text
handoff_batch_maturity_ci_regression_reason_counts=<json>
handoff_selected_batch_maturity_ci_regression_reason_counts=<json>
```

这样终端和 CI 日志可以直接看到 promotion 层保留的 reason-count 证据。

### `tests/test_training_scale_promotion.py`

测试 fixture 新增：

```text
batch_ci_regression_reason_counts
selected_batch_ci_regression_reason_counts
```

定向测试断言：

- promotion summary 保存 selected/global reason counts；
- CSV 输出 reason-count 字段和值；
- Markdown 和 HTML 展示 selected/global reason counts；
- CLI stdout 打印 selected/global reason-count JSON；
- strict clean-batch requirement 的 recommendation 包含 observed reason detail。

## 数据结构说明

handoff summary 输入示例：

```json
{
  "selected_batch_maturity_ci_regression_reason_counts": {
    "workflow-order-regressed": 1
  },
  "batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1,
    "workflow-order-regressed": 1
  }
}
```

promotion summary 输出示例：

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

前缀 `handoff_` 表示 promotion 层只是消费 handoff 证据，不重新分类 CI 回归原因。

## 运行流程

```text
build_training_scale_promotion()
        |
        v
load_training_scale_handoff()
        |
        v
_suite_guard()
  - read selected/global reason counts from handoff summary
        |
        v
_clean_batch_review_guard()
  - read aggregate reason counts for strict clean-batch review
        |
        v
_summary()
  - persist reason counts in promotion summary
        |
        v
write JSON / CSV / Markdown / HTML
        |
        v
scripts/build_training_scale_promotion.py
  - print reason-count JSON to stdout
```

promotion 层继续只做晋升审查，不执行训练、不重跑 benchmark，也不改变上游 handoff command。

## 测试覆盖

本版定向测试：

```text
python -m pytest tests/test_training_scale_promotion.py -q
```

覆盖点：

- completed handoff 仍可 promoted；
- failed handoff 仍 blocked；
- 缺少 variant artifact 仍进入 review；
- handoff suite guard 和 clean batch-review guard 语义保持；
- CI-regressed handoff batch evidence 会带 selected/global reason counts；
- strict clean batch-review requirement 因 CI regression 阻断时，recommendation 带 observed reason detail；
- facade 兼容 artifact exports。

## 证据归档

本版运行截图和说明放在：

```text
d/390/图片
d/390/解释/说明.md
```

`d/390/解释/v390-training-scale-promotion-maturity-ci-reasons-evidence.html` 是静态证据页，用于 Playwright MCP 截图；它不是最终机器消费源。

## 一句话总结

v390 把 maturity CI regression reason counts 从 workflow/handoff 推进到 promotion，让晋升审查报告也能直接解释 handoff CI 回归原因。

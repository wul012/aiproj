# v393 promoted training scale decision maturity CI reasons 代码讲解

## 本版目标和边界

v393 的目标是把 v392 promoted comparison 已经聚合出来的 selected/global/comparison-ready handoff maturity CI regression reason counts，继续带到 promoted training scale baseline decision。

promoted decision 是从 promoted comparison 选择下一轮 baseline 的入口。这个层会把 clean-required 且 CI-regressed 的 promoted input 排除在 baseline 候选之外。v393 让 decision 不只知道某个 input 被排除、排除 count 是多少，也能在 JSON、CSV、Markdown、HTML、CLI 和 recommendation 里说明具体 CI 回归原因分布。

本版不改变 baseline 选择排序，不改变 readiness/gate/batch/suite guard 规则，不改变 promoted seed 或 seed handoff。它只做证据字段贯通和报告可见性增强。

## 前置能力

本版承接 v384-v392 的 maturity CI reason 链路：

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
promotion
        |
        v
promotion index
        |
        v
promoted comparison
        |
        v
promoted baseline decision
```

v392 已经让 promoted comparison 区分 full-promotion reason counts 和 comparison-ready reason counts。v393 的作用是让 baseline decision 在选择下一轮 seed 前也保留这份解释能力。

## 关键文件

### `src/minigpt/promoted_training_scale_decision.py`

`_promotion_rows()` 新增读取：

```text
handoff_batch_maturity_ci_regression_reason_counts
handoff_selected_batch_maturity_ci_regression_reason_counts
```

这两个字段来自 promoted comparison rows。decision 层会继续把它们放到 `promotions`、`selected_baseline` 和 `rejected_runs`，因此被排除的 dirty CI input 仍能作为解释证据留在 report 里。

### `src/minigpt/promoted_training_scale_decision_review.py`

`build_decision_handoff_review_summary()` 新增四类 summary 字段：

```text
selected_handoff_batch_maturity_ci_regression_reason_counts
selected_handoff_selected_batch_maturity_ci_regression_reason_counts
handoff_batch_maturity_ci_regression_reason_counts
handoff_selected_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts
comparison_ready_handoff_selected_batch_maturity_ci_regression_reason_counts
```

其中 selected 字段说明最终 baseline 自身是否带有 CI reason evidence；full-promotion 字段说明所有 promoted inputs 的风险分布；comparison-ready 字段说明最终仍能参与 comparison 的输入是否还残留 CI reason evidence。

推荐语也会在 CI-regressed promoted inputs 被排除时输出 observed reasons，例如：

```text
Observed reasons: missing-ci-step:1, workflow-order-regressed:1.
```

### `src/minigpt/promoted_training_scale_decision_artifacts.py`

CSV 新增 selected/full/comparison-ready reason-count 字段。

Markdown summary 新增：

```text
Selected handoff batch CI regression reasons
Selected handoff selected batch CI regression reasons
Handoff batch CI regression reasons
Handoff selected batch CI regression reasons
Comparison-ready handoff batch CI regression reasons
Comparison-ready selected batch CI regression reasons
```

HTML stat cards 新增对应 reason cards。它们服务于人工审查；机器消费仍以 JSON summary 为准。

### `scripts/decide_promoted_training_scale_baseline.py`

stdout 新增 JSON 格式的 reason-count 输出：

```text
selected_handoff_batch_maturity_ci_regression_reason_counts=<json>
handoff_batch_maturity_ci_regression_reason_counts=<json>
comparison_ready_handoff_batch_maturity_ci_regression_reason_counts=<json>
```

这让 CI 日志或简单 shell reader 不必打开 HTML 就能判断被排除 input 的原因。

### `tests/test_promoted_training_scale_decision.py`

测试 fixture 在 dirty CI promoted input 上加入：

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

断言覆盖 rejected row、summary、CSV、Markdown、HTML、CLI stdout 和 recommendations。

## 数据结构说明

decision summary 示例：

```json
{
  "selected_handoff_batch_maturity_ci_regression_reason_counts": {},
  "handoff_batch_maturity_ci_regression_reason_counts": {
    "missing-ci-step": 1,
    "workflow-order-regressed": 1
  },
  "comparison_ready_handoff_batch_maturity_ci_regression_reason_counts": {}
}
```

这表示选中的 baseline 本身干净，dirty CI input 仍被记录在 full-promotion evidence 里，但没有进入 comparison-ready/baseline 候选路径。

## 运行流程

```text
build_promoted_training_scale_decision()
        |
        v
load promoted_training_scale_comparison.json
        |
        v
_promotion_rows()
  - carry row-level reason counts
  - preserve rejected dirty CI evidence
        |
        v
_rejection_reasons()
  - keep dirty clean-required CI inputs out of candidates
        |
        v
build_decision_handoff_review_summary()
  - selected/full/comparison-ready reason-count summaries
        |
        v
write JSON / CSV / Markdown / HTML
        |
        v
scripts/decide_promoted_training_scale_baseline.py
  - print reason-count JSON for CI logs
```

promoted decision 仍只选择 baseline，不执行训练，不生成下一轮 seed，也不修改 upstream comparison artifact。

## 测试覆盖

本版定向测试：

```text
python -m pytest tests/test_promoted_training_scale_decision.py -q
```

覆盖点：

- baseline 选择仍优先选择 clean/high-readiness promoted run；
- dirty CI promoted input 仍进入 `rejected_runs`，不进入候选；
- rejected row 保留 selected/global reason-count maps；
- summary 区分 selected/full/comparison-ready reason-count maps；
- CSV、Markdown、HTML、CLI stdout 展示 reason counts；
- recommendations 包含 observed reason detail。

## 证据归档

本版运行截图和说明放在：

```text
d/393/图片
d/393/解释/说明.md
```

`d/393/解释/v393-promoted-training-scale-decision-maturity-ci-reasons-evidence.html` 是静态证据页，用于 Playwright MCP 截图；它不是最终机器消费源。

## 一句话总结

v393 把 maturity CI regression reason counts 从 promoted comparison 推进到 promoted baseline decision，让下一轮 seed 选择前也能解释被排除 promoted input 的 CI 回归原因。

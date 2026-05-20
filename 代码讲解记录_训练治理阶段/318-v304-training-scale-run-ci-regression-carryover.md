# v304 training-scale run CI regression carryover

## 本版目标和边界

v304 解决的是 CI regression 证据在 batch 层之后可见性不足的问题。v301-v302 已经把 maturity narrative 的 CI workflow/order regression 传到 training portfolio comparison 和 training portfolio batch，但 gated training-scale run 与 run comparison 仍主要展示 coverage regression。

本版不改变训练、评估、gate 判定或 batch comparison 的原始逻辑，只把 batch 已经产生的 `maturity_ci_regression_count` 和 `maturity_ci_regression_names` 继续带到下游 run 与 run comparison 报告。

## 前置能力

前置链路是：

```text
maturity narrative -> training portfolio comparison -> training portfolio batch
```

v304 接上的下游链路是：

```text
training portfolio batch -> gated training-scale run -> training-scale run comparison
```

这样 CI 回归信号不会只停在 batch JSON/HTML 中，而能进入训练规模决策前的更高层汇总。

## 关键文件

- `src/minigpt/training_scale_run.py`
  - `_batch_summary()` 从 batch `comparison_review_summary` 读取 `maturity_ci_regression_count` 和 `maturity_ci_regression_names`。
  - CSV、Markdown、HTML 输出都展示 CI regression 字段。
  - recommendations 在存在 CI-regressed portfolios 时提醒不要把该 run 当成 clean automation evidence。

- `src/minigpt/training_scale_run_comparison.py`
  - `_run_summary()` 把 run-level CI regression 字段提升为 `batch_maturity_ci_regression_count/names`。
  - `_comparison_summary()` 聚合多 run 的 CI regression count 和 names。
  - recommendations 对 CI-regressed batch portfolios 给出单独提醒。

- `src/minigpt/training_scale_run_comparison_artifacts.py`
  - CSV 新增 `batch_maturity_ci_regression_count`。
  - Markdown summary 和 run table 展示 Batch CI regressions。
  - HTML stats 和 runs table 增加 CI regression 列。

- `scripts/run_training_scale_plan.py`
  - CLI 输出新增 `batch_summary=...`，让 smoke 日志可以直接看到 CI regression 字段。

- `tests/test_training_scale_run.py`
  - 构造带 CI regression 的 batch report，验证 `_batch_summary()`、Markdown 和 HTML 都保留 `ci-risk`。

- `tests/test_training_scale_run_comparison.py`
  - 构造 run report，验证 comparison summary、CSV、Markdown、HTML 均携带 batch CI regression 字段。

## 输入输出和字段语义

输入字段来自 batch review summary：

```json
{
  "maturity_ci_regression_count": 1,
  "maturity_ci_regression_names": ["ci-risk"]
}
```

run-level 输出继续使用同名字段：

```json
{
  "batch_summary": {
    "maturity_ci_regression_count": 1,
    "maturity_ci_regression_names": ["ci-risk"]
  }
}
```

comparison-level 输出使用 `batch_` 前缀，表示这是从每个 scale run 的 batch summary 聚合而来：

```json
{
  "summary": {
    "batch_maturity_ci_regression_count": 1,
    "batch_maturity_ci_regression_names": ["ci-risk"]
  }
}
```

这些字段是只读治理证据，不代表模型质量变好或变差；它们说明当前候选链路里存在 CI/workflow/order 方面的发布治理风险。

## 测试覆盖

本版测试覆盖两层：

- run 层测试确认 `_batch_summary()` 能从 batch review summary 取出 CI regression 字段，并且 Markdown/HTML 能渲染 `CI regressions` 和具体 portfolio 名称。
- comparison 层测试确认 `_run_summary()` 与 `_comparison_summary()` 能聚合 CI regression 字段，并且 CSV/Markdown/HTML 输出包含 `batch_maturity_ci_regression_count`。

邻近测试还覆盖 training portfolio batch 的既有 CI regression summary，不让上游字段来源漂移。

## 一句话总结

v304 把 batch 层 CI 回归证据继续传进训练规模 run 与 run comparison，让训练规模链路的下游入口也能看见自动化/CI 风险。

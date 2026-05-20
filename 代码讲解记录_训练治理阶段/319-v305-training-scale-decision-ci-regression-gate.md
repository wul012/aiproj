# v305 training-scale decision CI regression gate

## 本版目标和边界

v305 解决的是 CI regression 证据已经进入 training-scale run comparison，但还没有真正影响下一步 execute 决策的问题。v304 让 run comparison 可以聚合 `batch_maturity_ci_regression_count/names`，v305 则把这些字段接入 training-scale run decision。

本版不改变训练执行、gate 策略、readiness score 或 batch comparison 的计算方式。它只让决策层继续携带 CI regression 字段，并在 `--require-clean-batch-review` 打开时把 CI regression 纳入阻断条件。

## 前置能力

前置链路是：

```text
training portfolio batch -> gated training-scale run -> training-scale run comparison
```

v305 接上的下游链路是：

```text
training-scale run comparison -> training-scale run decision
```

这样 clean execution automation 不会只检查 review action、blocker 和 coverage regression，也会检查 CI/workflow/order regression。

## 关键文件

- `src/minigpt/training_scale_run_decision.py`
  - candidate/rejected row 增加 `batch_maturity_ci_regression_count`。
  - `_clean_batch_review_reasons()` 在严格模式下遇到 CI regression 会加入 `batch maturity CI regressions are present`。
  - `_decision_summary()` 增加 selected 和 aggregate 的 CI regression count/names。
  - `_batch_review_status()` 与 `_clean_batch_review_status()` 把 CI regression 视为 review 状态。
  - recommendations 提醒把 batch CI regression context 带入 promotion 和 automation review。

- `src/minigpt/training_scale_run_decision_artifacts.py`
  - CSV 新增 selected/aggregate CI regression 字段。
  - Markdown 新增 Selected batch CI regressions 和 Batch CI regressions。
  - HTML stats 新增 Selected CI regressions 和 CI regressions。

- `scripts/decide_training_scale_run.py`
  - CLI stdout 直接打印 `batch_maturity_ci_regression_count`、`selected_batch_maturity_ci_regression_count` 和 `clean_batch_review_status`。

- `tests/test_training_scale_run_decision.py`
  - 新增测试验证 CI regression 会让默认决策保持 review。
  - 新增测试验证 `require_clean_batch_review=True` 会阻断 CI-regressed comparison。
  - 新增测试验证 CSV/Markdown/HTML 都渲染 CI regression 字段。

## 输入输出和字段语义

输入来自 run comparison summary：

```json
{
  "batch_maturity_ci_regression_count": 1,
  "batch_maturity_ci_regression_names": ["ci-risk"]
}
```

decision summary 输出同时保留 aggregate 和 selected 视角：

```json
{
  "summary": {
    "selected_batch_maturity_ci_regression_count": 1,
    "batch_maturity_ci_regression_count": 1,
    "batch_maturity_ci_regression_names": ["ci-risk"],
    "clean_batch_review_status": "review"
  }
}
```

当 `require_clean_batch_review=True` 时，这种 review 状态会让 decision status 变成 `blocked`。这不是说模型能力失败，而是说明执行自动化要求 clean evidence 时，CI/workflow/order 风险没有清干净。

## 测试覆盖

本版测试覆盖三件事：

- CI regression 存在时，selected run 的 batch review status 是 `review`。
- 严格 clean batch-review gate 会因为 `batch maturity CI regressions are present` 阻断执行候选。
- CSV、Markdown、HTML 都能展示 selected 和 aggregate 的 CI regression 字段。

邻近测试还覆盖 run comparison 与 run summary 的上游字段，避免 v304 的字段来源失效。

## 一句话总结

v305 把 CI regression 从“可见的比较证据”推进成“可阻断的执行决策证据”，让训练规模自动化更接近 clean evidence 语义。

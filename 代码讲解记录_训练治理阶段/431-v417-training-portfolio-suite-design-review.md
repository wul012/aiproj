# v417 training portfolio suite-design review 代码讲解

## 本版目标与边界

v417 的目标是把 v416 maturity narrative 中的 release-readiness suite-design regression 用到 training portfolio comparison。之前训练组合比较已经能识别 coverage regression 和 CI regression，但如果最佳分数候选因为 benchmark suite-design readiness 出现回归，只能落入泛化的 maturity review。现在它会产生专门的 `best_score_suite_design_regressed` blocker。

本版不重新定义 suite-design 回归，不改 benchmark history、release readiness comparison、registry 或 maturity 的统计口径。它只消费 maturity narrative summary 已有字段，并把风险转成训练组合选择阶段的 review action。

## 前置链路

本版接在 v416 后面：

- v414 计算 release readiness comparison 的 suite-design delta。
- v415 将 delta 聚合到 registry。
- v416 将 registry suite-design regression 提升到 maturity summary/narrative。
- v417 将 maturity 中的 suite-design regression 用作 training portfolio comparison 的候选审查条件。

## 关键文件

### `src/minigpt/training_portfolio_comparison.py`

`_portfolio_summary()` 从 maturity narrative summary 读取新增字段：

- `release_readiness_benchmark_suite_design_delta_count`
- `release_readiness_benchmark_suite_design_regression_count`
- `release_readiness_benchmark_design_change_delta_count`
- `release_readiness_max_benchmark_suite_design_delta`
- `release_readiness_max_benchmark_design_change_delta`

并转为 portfolio 内部字段：

- `maturity_release_readiness_benchmark_suite_design_delta_count`
- `maturity_release_readiness_benchmark_suite_design_regression_count`
- `maturity_release_readiness_benchmark_design_change_delta_count`
- `maturity_release_readiness_max_benchmark_suite_design_delta`
- `maturity_release_readiness_max_benchmark_design_change_delta`

`_portfolio_delta()` 新增 suite-design 相关 delta：

- `maturity_release_readiness_benchmark_suite_design_delta_count_delta`
- `maturity_release_readiness_benchmark_suite_design_regression_delta`
- `maturity_release_readiness_benchmark_design_change_delta`

`_comparison_summary()` 汇总 suite-design regression portfolio：

- `maturity_suite_design_regression_count`
- `maturity_suite_design_regression_names`
- best-score candidate 的 suite/design 字段

这样 summary 可以在不打开每个 maturity narrative 的情况下说明哪个训练组合存在 suite-design 风险。

### `src/minigpt/training_portfolio_comparison_review.py`

新增 `BENCHMARK_REGRESSED_TREND` 和 `has_maturity_suite_design_regression()`。

当 portfolio 同时满足：

```text
maturity_release_readiness_trend == "benchmark-regressed"
maturity_release_readiness_benchmark_suite_design_regression_count > 0
```

就会生成 suite-design review action。若该 portfolio 是 best-score candidate，severity 是 `blocker`，reason 是 `best_score_suite_design_regressed`；否则是 `portfolio_suite_design_regressed`。

这个判断放在泛化 maturity review 之前，因此 suite-design 风险不会被淹没在 `best_score_maturity_review` 里。

### `src/minigpt/training_portfolio_comparison_artifacts.py`

CSV、Markdown 和 HTML 都新增 suite-design 字段：

- CSV 字段保存每个 portfolio 的 suite/design 计数和 delta。
- Markdown summary 显示 suite-design regression count 和 portfolio names。
- HTML stat cards 显示 `Suite-design regressions` 和 `Suite-design portfolios`。
- Portfolio row 的 maturity cell 显示 `suite=<n>`。

### `scripts/compare_training_portfolios.py`

CLI stdout 增加：

```text
maturity_suite_design_regression_count
maturity_suite_design_regression_names
```

这样命令行运行时不需要打开 JSON 也能看到 suite-design 风险是否进入比较结果。

## 测试覆盖

`tests/test_training_portfolio_comparison.py` 新增 best-score suite-design regression 场景：

- baseline 是稳定 portfolio。
- candidate 分数更高、final val loss 更低。
- candidate maturity trend 是 `benchmark-regressed`，suite-design regression count 为 1。

断言重点：

- summary 记录 `maturity_suite_design_regression_count=1`。
- best-score candidate 是 candidate。
- review action 是 `best_score_suite_design_regressed`。
- severity 是 `blocker`。
- delta explanation 包含 `release-readiness suite-design regressed`。
- renderer、CSV 和 CLI stdout 都能看到 suite-design 字段。

本轮验证：

- 定向训练组合比较测试：`10 passed`
- 全量测试：`708 passed`
- source encoding hygiene：`status=pass`
- 语法编译与 diff 检查：通过

## 运行证据

`d/417` 归档了本版截图和说明：

- `d/417/图片/01-training-portfolio-suite-design-review-evidence.png`
- `d/417/解释/v417-training-portfolio-suite-design-review-evidence.html`
- `d/417/解释/说明.md`

截图证明 candidate 虽然是 best score 和 best val loss，但因为 suite-design regression，被 comparison review action 标为 blocker。

一句话总结：v417 让 suite-design readiness regression 真正参与训练候选选择，而不是只停留在成熟度报告展示层。

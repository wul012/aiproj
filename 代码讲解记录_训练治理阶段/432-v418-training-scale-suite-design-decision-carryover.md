# v418 training scale suite-design decision carryover 代码讲解

## 本版目标与边界

v418 的目标是把 v417 已经识别出的 suite-design regression blocker 从 training portfolio batch 层继续带到 training scale run、scale-run comparison、decision 和 workflow。这样后续执行决策看到 batch blocker 时，可以同时看到 `batch_maturity_suite_design_regression_count` 和 affected portfolio names，而不是只知道有 blocker。

本版不新增 benchmark 规则，不改变训练执行，也不重新解释 suite-design readiness。它只消费 `training_portfolio_comparison` summary 中已有的 `maturity_suite_design_regression_*` 字段，并在下游报告里保持这个字段不丢失。

## 前置链路

本版接在 v417 后面：

- v414-v416 把 release-readiness suite-design delta 逐步带入 registry 和 maturity narrative。
- v417 让 training portfolio comparison 把 suite-design regression 转为 dedicated blocker action。
- v418 负责把这个 blocker 的原因和 portfolio 名称带入 scale-run execution decision 层。

## 关键文件

### `src/minigpt/training_portfolio_batch.py`

`_comparison_review_summary()` 新增读取：

- `maturity_suite_design_regression_count`
- `maturity_suite_design_regression_names`

它的输入是 `build_training_portfolio_comparison()` 产生的 comparison report。v417 已经让该 report summary 拥有 suite-design regression 字段，所以 batch 层只需要把字段放进 `comparison_review_summary`，供 scale run 的 `_batch_summary()` 使用。

### `src/minigpt/training_portfolio_batch_artifacts.py`

Markdown 和 HTML 增加 suite-design regression 展示：

- 顶部摘要显示 `Suite-design regressed portfolios`
- Comparison panel 显示 `Suite-design regressions`
- HTML stats 显示 suite-design regression count

这些输出不是新的判定来源，只是把 batch review summary 里的机器字段转成人可读证据。

### `src/minigpt/training_scale_run.py`

`_batch_summary()` 从 batch report 的 `comparison_review_summary` 里带出：

- `maturity_suite_design_regression_count`
- `maturity_suite_design_regression_names`

skipped batch 的默认值是 `0` 和空列表，保证 blocked gate、skipped batch 等旧场景仍保持稳定 schema。

CSV、Markdown 和 HTML 也加入 suite-design regression 字段。`_recommendations()` 在发现 suite-design regression 时提示它是 benchmark evidence 风险，而不是训练执行本身的崩溃。

### `src/minigpt/training_scale_run_comparison.py`

每个 run summary 新增：

- `batch_maturity_suite_design_regression_count`
- `batch_maturity_suite_design_regression_names`

comparison summary 会聚合 count，并对 names 去重排序。这样多个 gate profile 或多个 scale run 被比较时，最终报告可以说明哪些 batch portfolio 因 suite-design regression 需要 review。

### `src/minigpt/training_scale_run_comparison_artifacts.py`

CSV 增加 `batch_maturity_suite_design_regression_count`。Markdown 和 HTML 的 summary/table 也显示 suite-design regression count。

这个文件只负责 artifact 渲染，不参与决策逻辑。

### `src/minigpt/training_scale_run_decision.py`

decision summary 新增 selected/global 两组字段：

- `selected_batch_maturity_suite_design_regression_count`
- `selected_batch_maturity_suite_design_regression_names`
- `batch_maturity_suite_design_regression_count`
- `batch_maturity_suite_design_regression_names`

`_clean_batch_review_reasons()` 现在把 suite-design regression 视为 maturity-regression evidence；如果用户开启 `--require-clean-batch-review`，它会成为阻断原因之一。默认决策不会直接隐藏 selected run，而是保留 selected run 并把 decision status 降为 `review`，方便人工看到“为什么不能直接执行”。

### `src/minigpt/training_scale_run_decision_artifacts.py`

CSV、Markdown、HTML 增加 selected/global suite-design regression 字段。这样 JSON、表格、页面截图和命令行日志都能说明 blocker 的来源。

### `src/minigpt/training_scale_workflow.py`

workflow summary 从 decision summary 继续带出 selected/global suite-design regression 字段，并在 recommendations 中提示要检查 suite-design regressed batch evidence。这样 consolidated workflow 不会把 decision 层的 suite-design blocker 吃掉。

### `src/minigpt/training_scale_workflow_artifacts.py`

workflow CSV、Markdown、HTML 增加 suite-design regression count 和 names。它服务于整体工作流交接，不改变 plan、gate、run、comparison 或 decision 的执行顺序。

### CLI 脚本

三个脚本增加 stdout 诊断字段：

- `scripts/compare_training_scale_runs.py`
- `scripts/decide_training_scale_run.py`
- `scripts/run_training_scale_workflow.py`

新增输出让 CI 日志或 shell 调用不用打开 JSON，也能看到 suite-design regression 是否进入 scale-run 决策链。

## 核心数据流

本版字段流向是：

```text
training_portfolio_comparison.summary
  -> training_portfolio_batch.comparison_review_summary
  -> training_scale_run.batch_summary
  -> training_scale_run_comparison.runs/summary
  -> training_scale_run_decision.summary
  -> training_scale_workflow.summary
  -> JSON/CSV/Markdown/HTML/CLI evidence
```

关键字段命名保持分层：

- batch 内部使用 `maturity_suite_design_regression_*`
- scale-run comparison 使用 `batch_maturity_suite_design_regression_*`
- decision selected 字段使用 `selected_batch_maturity_suite_design_regression_*`

这样读字段名就能知道它来自哪个层级。

## 测试覆盖

本版补了五组测试：

- `tests/test_training_portfolio_batch.py`：确认 batch review summary 会带出 suite-design regression count/names，并被 batch renderer 展示。
- `tests/test_training_scale_run.py`：确认 `_batch_summary()`、Markdown、HTML 能显示 suite-design regression。
- `tests/test_training_scale_run_comparison.py`：确认 run row 和 comparison summary 聚合 suite-design regression，并写入 CSV/Markdown/HTML。
- `tests/test_training_scale_run_decision.py`：确认 decision selected/global summary、clean batch-review gating、CLI stdout 和 artifact renderers 都包含 suite-design 字段。
- `tests/test_training_scale_workflow.py`：确认 workflow summary、recommendations、CSV、Markdown、HTML 和 CLI stdout 都保留 suite-design regression。

本轮验证：

- 相关测试：`49 passed`
- 全量测试：通过
- source encoding hygiene：`status=pass`
- 语法编译和 `git diff --check`：通过

## 运行证据

`d/418` 归档了本版截图和说明：

- `d/418/图片/01-training-scale-suite-design-decision.png`
- `d/418/解释/v418-training-scale-suite-design-decision-evidence.html`
- `d/418/解释/v418-training-scale-suite-design-decision-snapshot.md`
- `d/418/解释/说明.md`

截图中的关键状态是：

- decision status 为 `review`
- clean batch review status 为 `blocker`
- selected/global suite-design regression count 都是 `1`

这说明 suite-design blocker 没有在 batch 到 decision 的链路中丢失。

一句话总结：v418 把 suite-design regression 从训练组合候选审查推进到训练规模执行决策证据，让后续 handoff 能解释 blocker 原因，而不是只传一个总数。

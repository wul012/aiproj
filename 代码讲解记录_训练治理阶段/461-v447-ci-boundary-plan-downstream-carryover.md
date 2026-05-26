# v447 CI boundary plan downstream carryover

## 本版目标和边界

v446 已经让 release readiness comparison 能发现 ready-vs-ready 场景中的 CI boundary plan-check readiness regression。v447 的目标是把这条 regression 继续传到下游：registry 汇总、maturity summary、maturity narrative、training portfolio comparison，以及最终 review action。

本版不新增新的治理链，不重新训练模型，不把 CI 契约问题解释成模型质量问题，也不改变 candidate 是否被 scorecard 选为 best-score。它解决的是证据链断点：如果 `boundary_gate_plan_check_not_ready` 只停留在 comparison JSON 里，下游成熟度和组合评审就可能继续把高分候选当成可推进对象。

## 前置链路

本版承接 v445-v446：

- v445：CI workflow hygiene 的 boundary gate/check ready 字段进入 project audit、release bundle 和 release readiness。
- v446：release readiness comparison 把 boundary plan-check ready -> not ready 映射成 `boundary_gate_plan_check_not_ready` regression reason。
- v447：registry 与 maturity 链路消费该 reason/count，并让 training portfolio comparison 的 best-score review action 直接看到它。

## 关键文件

- `src/minigpt/registry_release_readiness.py`
  - 新增 `CI_READY_REGRESSION_REASON_FIELDS`，集中维护四类 CI ready regression 字段与 reason 的映射。
  - `collect_release_readiness_delta_rows()` 把 tiny plan digest、boundary gate check、boundary plan check、drift-contract smoke 的 regressed flag 写入 row。
  - `release_readiness_delta_summary()` 统计四类 ready regression count。
  - `_ci_workflow_regression_reasons()` 使用统一映射生成稳定 reason，避免只处理 drift smoke 的单点逻辑。
- `src/minigpt/maturity.py`
  - `_release_readiness_context()` 从 registry delta summary 读取四类 ready regression count。
  - `_summary()` 将这些字段提升到 maturity summary 顶层，供脚本、Markdown、HTML、narrative 继续消费。
- `src/minigpt/maturity_artifacts.py`
  - Markdown Overview 和 Release Readiness Trend Context 增加四类 CI ready regression rows。
  - HTML stats 与 release readiness section 增加 boundary plan regression 可视化字段。
- `src/minigpt/maturity_narrative_summary.py`
  - `_release_summary()` 从 maturity summary 和 release context 中合并四类 count。
  - narrative summary 顶层输出 `release_readiness_ci_boundary_plan_check_ready_regression_count` 等字段。
- `src/minigpt/maturity_narrative_artifacts.py`
  - Markdown portfolio summary 和 HTML stats 展示 release CI boundary plan regression。
- `src/minigpt/maturity_narrative_sections.py`
  - 发布质量 claim 中加入 `CI boundary plan regressions=N`，让人工读 narrative 时不必打开 JSON。
- `src/minigpt/training_portfolio_comparison.py`
  - `_portfolio_summary()` 从 maturity narrative artifact 中读取四类 ready regression count。
  - `_comparison_summary()` 将 best-score candidate 的 boundary plan regression count 提升到 summary。
- `src/minigpt/training_portfolio_comparison_review.py`
  - `has_maturity_ci_regression()` 把四类 ready regression count 纳入 CI regression 判断。
  - `build_training_portfolio_review_actions()` 在 blocker action evidence 中写入 `ci_boundary_plan_check_ready_regression_count`。
  - best-score recommendation 现在会因为 boundary plan regression count 大于 0 而阻止 promotion。
- `src/minigpt/training_portfolio_comparison_artifacts.py`
  - CSV、Markdown、HTML 展示 portfolio 层和 best-score summary 层的 boundary plan count。
- `scripts/register_runs.py`
  - CLI stdout 打印 `release_readiness_ci_boundary_plan_check_ready_regression_count`。
- `scripts/build_maturity_summary.py`
  - CLI stdout 打印四类 release readiness CI ready regression count。
- `scripts/build_maturity_narrative.py`
  - CLI stdout 打印同一组 narrative summary 字段。
- `scripts/compare_training_portfolios.py`
  - CLI stdout 打印 `best_score_maturity_release_readiness_ci_boundary_plan_check_ready_regression_count`。

## 核心字段

registry delta summary 里新增或继续透传的字段是：

- `ci_workflow_tiny_scorecard_plan_digest_gate_ready_regression_count`
- `ci_workflow_baseline_candidate_threshold_boundary_gate_check_ready_regression_count`
- `ci_workflow_baseline_candidate_threshold_boundary_gate_plan_check_ready_regression_count`
- `ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count`

maturity summary 和 maturity narrative 中使用更短的下游字段名：

- `release_readiness_ci_tiny_plan_digest_gate_ready_regression_count`
- `release_readiness_ci_boundary_gate_check_ready_regression_count`
- `release_readiness_ci_boundary_plan_check_ready_regression_count`
- `release_readiness_ci_drift_smoke_ready_regression_count`

training portfolio comparison 中再加上 portfolio 前缀：

- `maturity_release_readiness_ci_boundary_plan_check_ready_regression_count`
- `best_score_maturity_release_readiness_ci_boundary_plan_check_ready_regression_count`

这些字段的语义都很窄：它们表示 release readiness CI 契约门是否发生 ready -> not ready 的回归，不表示模型生成质量下降，也不替代 benchmark score。

## 运行流程

1. release readiness comparison 产出 delta，其中 boundary plan check regressed 为 `True`。
2. `scripts/register_runs.py` 读取 run 目录，把 comparison delta 转为 registry row 和 delta summary。
3. `scripts/build_maturity_summary.py` 从 registry 中提取 release readiness context，并把 boundary plan regression count 放进 maturity summary。
4. `scripts/build_maturity_narrative.py` 从 maturity summary 生成发布质量叙事，保留相同 count 与 reason。
5. `scripts/compare_training_portfolios.py` 读取 candidate 的 maturity narrative。
6. candidate 虽然是 best-score，但 review layer 因 `ci_boundary_plan_check_ready_regression_count=1` 生成 blocker action。

## 测试覆盖

本版聚焦测试覆盖 6 个测试文件，共 `67 passed`：

- `tests/test_registry.py`
  - fixture 支持 boundary plan regression。
  - registry CLI/stdout 与输出字段继续可读。
- `tests/test_registry_rankings.py`
  - release readiness delta summary 统计 boundary plan regression count。
  - leaderboard row 保留 regressed flag 和 reason。
- `tests/test_maturity.py`
  - maturity summary 和 release readiness context 输出 boundary plan regression count。
  - Markdown/HTML 输出能读到 boundary plan regressions。
- `tests/test_maturity_narrative.py`
  - narrative summary、release section claim、recommendation 都保留 `boundary_gate_plan_check_not_ready`。
- `tests/test_training_portfolio_comparison.py`
  - best-score candidate 带 boundary plan regression 时，summary 和 review action 必须记录 blocker。
  - CSV/Markdown/HTML 都暴露 best-score CI boundary plan count。
- `tests/test_training_portfolio_comparison_review.py`
  - `has_maturity_ci_regression()` 对单独的 boundary plan count 返回 true。
  - blocker action evidence 保留 `ci_boundary_plan_check_ready_regression_count=1`。

收口验证还跑了：

- 全量测试：`780 passed`
- source encoding hygiene：`source_count=351`，`clean_count=351`
- `git diff --check`：无 whitespace error

## 运行证据

`d/447` 保存了本版证据：

- `registry-fixture/boundary-plan/`：受控 run fixture，模拟 boundary plan-check regression。
- `registry/register_runs_stdout.txt`：显示 registry 层 `release_readiness_ci_boundary_plan_check_ready_regression_count=1`。
- `maturity-summary/maturity_summary.json` 与 `maturity_summary_stdout.txt`：显示 maturity 层 `release_readiness_ci_boundary_plan_check_ready_regression_count=1`。
- `maturity-narrative/maturity_narrative.json` 与 `maturity_narrative_stdout.txt`：显示 narrative 层继续保留该 count。
- `training-portfolio-comparison/training_portfolio_comparison.json`：best-score summary 中 `best_score_maturity_release_readiness_ci_boundary_plan_check_ready_regression_count=1`。
- `training_portfolio_comparison_snapshot.md` 和 `图片/01-training-portfolio-boundary-plan-review.png`：Playwright MCP 证明 HTML 中可见 `Best score CI boundary plan = 1`、`Blocker actions = 1` 和 `boundary_gate_plan_check_not_ready:1`。

## 一句话总结

v447 把 CI boundary plan-check regression 从 release readiness comparison 推到 registry、maturity、narrative 和 training portfolio review，使高分候选也必须带着发布契约回归证据接受 blocker 级审查。

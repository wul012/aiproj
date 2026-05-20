# 313. v299 registry and maturity CI order regression summary

## 本版目标与边界

v299 的目标是把 v298 的 release-readiness comparison order regression 继续传入 registry 和 maturity 汇总，让跨版本 CI 顺序治理不止停留在 comparison 报告，而是能进入项目总览和成熟度视图。

本版不改变训练、发布或 comparison 的核心判定逻辑，也不新增新的报表家族。它只把现有 order regression 字段继续往上游汇总和展示。

## 前置链路

v296 把 order counts 送入 project audit。v297 把它们送进 release bundle/readiness。v298 把 order violation 送进 readiness comparison。

v299 进一步把 v298 的 comparison summary 接入 registry 和 maturity：

- registry summary 能看见 `release_readiness_ci_workflow_order_regression_count`
- registry rows / leaderboard 能看见 `ci_workflow_order_violation_delta`
- maturity summary / HTML / Markdown 能看见 `release_readiness_ci_workflow_order_regression_count`

## 关键文件

- `src/minigpt/registry_rankings.py`
  - `collect_release_readiness_delta_rows()` 增加 `ci_workflow_required_order_delta` 和 `ci_workflow_order_violation_delta`。
  - `release_readiness_delta_leaderboard()` 将 order violation delta 纳入排序权重。
  - `release_readiness_delta_summary()` 新增 `ci_workflow_order_regression_count` 和 `max_abs_ci_workflow_order_violation_delta`。
  - `_is_ci_workflow_regression_row()` 把 order violation 增加视为 regression。

- `src/minigpt/registry_data.py`
  - `RegisteredRun` 新增 `release_readiness_ci_workflow_order_regression_count`。
  - `summarize_registered_run()` 从 release readiness comparison summary 读取这个字段。

- `src/minigpt/registry_artifacts.py`
  - registry CSV 增加 `release_readiness_ci_workflow_order_regression_count`。

- `src/minigpt/registry_render.py`
  - registry overview 里显示 `CI order regressions`。
  - 每个 run 的 release readiness cell 里显示 `ci order regressions=...`。

- `src/minigpt/registry_leaderboards.py`
  - release readiness delta leaderboard 显示 order violation delta。

- `src/minigpt/maturity.py`
  - maturity summary 把 order regression count 与 max order violation delta 继续带到顶层摘要。
  - `release_readiness_context` 在缺失和存在两种情况下都保留这些字段。

- `src/minigpt/maturity_artifacts.py`
  - Markdown、HTML 和 section 视图都增加 CI order regression / max order-violation delta。

- `tests/test_registry.py`、`tests/test_registry_rankings.py`、`tests/test_maturity.py`
  - 分别验证 registry summary、leaderboard、maturity summary 都能看到新字段。

## 输入输出

registry 的 release readiness delta summary 现在会输出：

```text
ci_workflow_order_regression_count=1
max_abs_ci_workflow_order_violation_delta=1
```

registry rows 也会保留：

```text
ci_workflow_order_violation_delta=1
```

maturity summary 顶层则会显示：

```text
release_readiness_ci_workflow_order_regression_count=1
release_readiness_max_ci_workflow_order_violation_delta=1
```

## 测试与证据

本版运行了以下验证：

- `python -B -m unittest tests.test_registry tests.test_registry_rankings tests.test_maturity`
  - 21 个聚焦测试通过。
- `python -B -m py_compile ...`
  - registry / maturity 相关脚本和模块语法通过。
- `python -B -m unittest discover -s tests`
  - 全量测试会在最终收口阶段再跑一次并写入证据截图。

运行截图和解释归档在 `c/299`。其中 registry screenshot 证明 summary、row 和 leaderboard 都看得到 order regression；maturity screenshot 证明顶层成熟度视图也能消费这条指标。

## 链路角色

v299 让 release-readiness comparison 的 order violation 不再只停留在对比层，而是进入 registry 和 maturity 的总览层，成为项目级治理信号。

一句话总结：v299 把 CI workflow order regression 从 comparison 报告推进到 registry 和 maturity 汇总，让项目总览也能感知 smoke-before-coverage 漂移。

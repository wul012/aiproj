# 第一百五十版代码讲解：registry CI workflow readiness regression tracking

## 本版目标

v150 的目标是把 v149 已经进入 release readiness comparison 的 CI workflow regression 继续汇总进 run registry。

v145 到 v149 的链路已经让 CI workflow hygiene 从独立检查进入 audit、bundle、readiness dashboard 和 readiness comparison。v150 解决的是更上层的 run 总览问题：当 registry 聚合多个 run 时，也应该能看到哪个 run 的 release readiness comparison 出现了 CI workflow hygiene regression。

本版不修改 GitHub Actions workflow，不改变 release gate 硬规则，不改模型、训练、推理或 benchmark 逻辑。

## 前置路线

本版承接：

```text
v145 -> ci_workflow_hygiene gate
v146 -> project_audit CI context
v147 -> release_bundle CI evidence
v148 -> release_readiness CI panel
v149 -> release_readiness_comparison CI deltas
v150 -> registry CI readiness regression tracking
```

这让 CI workflow hygiene 从“当前版本的一条检查”变成“可以跨 run 总览的治理信号”。

## 关键文件

```text
src/minigpt/registry_data.py
src/minigpt/registry_rankings.py
src/minigpt/registry_render.py
src/minigpt/registry_artifacts.py
tests/test_registry.py
tests/test_registry_rankings.py
README.md
c/150/解释/说明.md
```

`registry_data.py` 负责把 release readiness comparison summary 读进 `RegisteredRun`。

`registry_rankings.py` 负责把 comparison delta 行抽出来、排序并生成 release readiness delta summary。

`registry_render.py` 负责把 registry HTML 的 Release Readiness cell 和 Release Readiness Deltas 表格展示出来。

`registry_artifacts.py` 负责 registry CSV 字段。

## 核心数据结构

`RegisteredRun` 新增字段：

```text
release_readiness_ci_workflow_regression_count
```

registry CSV 新增同名列。

release readiness delta row 新增字段：

```text
baseline_ci_workflow_status
compared_ci_workflow_status
ci_workflow_failed_check_delta
ci_workflow_status_changed
```

release readiness delta summary 新增字段：

```text
ci_workflow_regression_count
ci_workflow_status_changed_count
max_abs_ci_workflow_failed_check_delta
```

这些字段来自 v149 的 `release_readiness_comparison.json`，registry 不重新解析 workflow。

## Registry 状态边界

`_release_readiness_comparison_status()` 新增：

```text
ci-regressed
```

当 comparison summary 的 `ci_workflow_regression_count > 0` 时，registry run 的 release readiness status 会是 `ci-regressed`。

这个状态和 `regressed` 分开，是为了表达边界：

- `regressed` 更偏 release readiness 整体状态退化。
- `ci-regressed` 表示 CI workflow hygiene 出现退化，但 release gate 规则没有改变。

## 排序和汇总

`release_readiness_delta_leaderboard()` 在排序时把 CI workflow status change 和 failed-check delta 纳入优先级：

```text
delta_status priority
ci_workflow_status_changed
abs(ci_workflow_failed_check_delta)
abs(status_delta)
changed_panel_count
```

这保证带 CI workflow 退化的 readiness delta 更容易出现在 registry HTML 的 Release Readiness Deltas 表格前面。

## 输出展示

registry HTML 的 Release Readiness cell 新增：

```text
ci regressions=<n>
```

Release Readiness Deltas 表格新增 CI workflow 列：

```text
baseline_ci_workflow_status -> compared_ci_workflow_status
failed=<delta>
```

CSV 新增：

```text
release_readiness_ci_workflow_regression_count
```

registry JSON 则通过 `RegisteredRun.to_dict()` 自动携带新增字段。

## 测试覆盖

`tests/test_registry.py` 覆盖：

- `summarize_registered_run()` 能读到 CI workflow regression count。
- 当 CI workflow regression 存在时，run status 是 `ci-regressed`。
- registry summary 能汇总 `ci_workflow_regression_count`。
- registry leaderboard delta row 能携带 `ci_workflow_failed_check_delta`。
- CSV 和 HTML 都包含新增字段和展示文案。

`tests/test_registry_rankings.py` 覆盖：

- release readiness delta summary 汇总 CI workflow regression count。
- max failed-check delta 正确计算。
- leaderboard row 保留 CI workflow failed-check delta。

## 截图与归档

v150 的运行截图和解释放在 `c/150`：

- `01-registry-tests.png`
- `02-registry-cli-smoke.png`
- `03-ci-workflow-hygiene-smoke.png`
- `04-source-encoding-smoke.png`
- `05-maintenance-smoke.png`
- `06-full-unittest.png`
- `07-docs-check.png`

这些证据证明 registry 能消费 v149 comparison 的 CI workflow delta，同时全量测试、源码 hygiene、CI workflow hygiene 和维护 smoke 仍然通过。

## 一句话总结

v150 把 CI workflow hygiene regression 从 release readiness comparison 推进到 registry 总览，让多个 run 的治理页面也能发现 CI 策略退化。

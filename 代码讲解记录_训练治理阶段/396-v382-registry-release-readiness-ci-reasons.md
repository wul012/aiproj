# v382 registry release readiness CI reasons 代码讲解

## 本版目标和边界

v382 的目标是把 v381 产生的 CI workflow regression reason 带入 run registry。

v381 只解决了单个 release readiness comparison artifact 内部“为什么 CI 回归”的问题。v382 解决的是多 run 扫描问题：registry 汇总多个 run 的 comparison delta 时，也要保留 reason list 和 reason counts，否则 reviewer 到 registry 层又只能看到 `ci_workflow_regression_count=1` 这样的粗粒度数字。

本版不新增新的 report 类型，不改变 release readiness comparison schema，不向 maturity/narrative 继续传播，也不改变 registry 的排序主逻辑。

## 前置能力

本版承接 v381：

```text
release_readiness_comparison.delta.ci_workflow_regression_reasons
        |
        v
registry_release_readiness.collect_release_readiness_delta_rows()
        |
        v
registry.release_readiness_delta_summary.ci_workflow_regression_reason_counts
        |
        v
registry CSV / HTML / CLI / leaderboard
```

## 关键文件

### `src/minigpt/registry_release_readiness.py`

`collect_release_readiness_delta_rows()` 新增：

```text
ci_workflow_regression_reasons
```

如果新 comparison delta 已经有 reason list，就直接读取；如果是旧 artifact 没有这个字段，则从以下字段推导：

```text
ci_workflow_failed_check_delta
ci_workflow_order_violation_delta
ci_workflow_release_readiness_drift_contract_smoke_ready_regressed
ci_workflow_status_changed + baseline/compared status
```

summary 新增：

```text
ci_workflow_regression_reasons
ci_workflow_regression_reason_counts
```

这样 registry 能跨多个 run 统计 CI 回归类型。

### `src/minigpt/registry_data.py`

`RegisteredRun` 新增：

```text
release_readiness_ci_workflow_regression_reasons
```

run 级字段从 release readiness comparison summary 读取，用于 CSV 和 HTML 单 run 单元格。

### `src/minigpt/registry_artifacts.py`

registry CSV 新增：

```text
release_readiness_ci_workflow_regression_reasons
```

列表字段会通过既有 `_csv_value()` 写成分号分隔字符串。

### `src/minigpt/registry_render.py`

HTML stats 新增 `CI regression reasons`。Release Readiness 单元格新增：

```text
ci reasons=...
```

这让 registry 页面不用打开 comparison JSON 就能看见 reason。

### `src/minigpt/registry_leaderboards.py`

Release Readiness Deltas leaderboard 的 CI workflow 列新增：

```text
reasons=...
```

这样最严重 delta 排名前列能同时展示 CI 状态、failed/order delta 和 reason list。

### `scripts/register_runs.py`

stdout 新增：

```text
release_readiness_ci_regression_reason_counts={...}
```

CI log 或本地 shell 能直接看到 registry 级 reason 聚合。

## 测试覆盖

`tests/test_registry.py` 覆盖两条路径：

- 新 artifact 路径：summary 和 delta 都带 `ci_workflow_regression_reasons`，registry 原样聚合。
- 旧 artifact 兼容路径：delta 没有 reason list，但有 `ci_workflow_release_readiness_drift_contract_smoke_ready_regressed=True`，registry 推导出 `drift_contract_smoke_not_ready`。

阶段验证：

```text
16 passed
```

最终全量验证：

```text
680 passed
```

source encoding hygiene：

```text
status=pass
source_count=312
clean_count=312
bom_count=0
syntax_error_count=0
```

## 运行证据

运行证据归档在：

```text
d/382/图片/01-registry-release-readiness-ci-reasons-evidence.png
d/382/解释/说明.md
```

证据页展示 registry summary、CLI 输出字段、HTML/leaderboard 展示位置和测试结果。

## 一句话总结

v382 让 release readiness CI regression reasons 从单个 comparison artifact 进入 registry 多 run 视角，使 registry 也能说明 CI 回归到底由什么原因组成。

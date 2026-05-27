# v465 release readiness archived path regression 代码讲解

## 本版目标和边界

v465 的目标是让 release readiness comparison 比较 `ci_workflow_archived_path_portability_check_ready`。当 baseline 是 `True`，current 变成 `False` 或缺失时，comparison 要把它标记为 CI workflow regression。

它解决的问题是：v464 已经让单个 readiness 报告能看到 archived path portability readiness，但多版本对比还不能发现这条 readiness 的退化。

本版不改 v463 的路径扫描规则，不改 v464 的 audit/bundle/readiness carryover，也不改变 release readiness 的总状态判定。整体仍是 `ready` 的两个报告，也可以因为 archived path portability 退化而产生 CI regression reason。

## 前置能力

本版承接 v463-v464：

- v463：新增 archived path portability CI gate。
- v464：把 `archived_path_portability_check_ready` 带入 audit、bundle、readiness。
- v465：把 readiness summary 里的 `ci_workflow_archived_path_portability_check_ready` 带入 comparison rows 和 deltas。

## 关键修改文件

### `src/minigpt/release_readiness_comparison.py`

`_row_from_report()` 新增字段：

```text
ci_workflow_archived_path_portability_check_ready
```

`_delta_from_baseline()` 新增四个 delta 字段：

```text
baseline_ci_workflow_archived_path_portability_check_ready
compared_ci_workflow_archived_path_portability_check_ready
ci_workflow_archived_path_portability_check_ready_changed
ci_workflow_archived_path_portability_check_ready_regressed
```

退化判断沿用既有 CI readiness 规则：

```text
baseline is True and compared is not True
```

`_ci_workflow_regression_reasons()` 新增 reason：

```text
archived_path_portability_check_not_ready
```

`_summary()` 新增 changed/regression 计数：

```text
ci_workflow_archived_path_portability_check_ready_changed_count
ci_workflow_archived_path_portability_check_ready_regression_count
```

### `src/minigpt/release_readiness_comparison_artifacts.py`

CSV、Markdown、HTML 都新增 archived path readiness 列：

- rows CSV：`ci_workflow_archived_path_portability_check_ready`
- delta CSV：baseline/compared/changed/regressed 四个字段
- Markdown Summary：archived path changes/regressions
- Markdown Matrix：`CI archived paths`
- Markdown Deltas：`CI archived paths changed/regressed`
- HTML stats、matrix、delta table 同步展示

这些 artifact 是展示和复核层，不负责重新判断 regression。

### `scripts/compare_release_readiness.py`

CLI 新增两行输出：

```text
ci_workflow_archived_path_portability_check_ready_changed_count
ci_workflow_archived_path_portability_check_ready_regression_count
```

这样 shell 日志不打开 JSON 也能判断本版能力是否生效。

### `src/minigpt/registry_release_readiness.py`

`CI_READY_REGRESSION_REASON_FIELDS` 新增：

```text
ci_workflow_archived_path_portability_check_ready_regressed
  -> archived_path_portability_check_not_ready
```

这一步让 registry/maturity 后续读取 release readiness comparison 时，也能把 archived path readiness 回归纳入 CI regression reason 汇总。

## 数据流

```text
release_readiness.summary.ci_workflow_archived_path_portability_check_ready
  -> comparison.rows[*].ci_workflow_archived_path_portability_check_ready
  -> comparison.deltas[*].ci_workflow_archived_path_portability_check_ready_regressed
  -> comparison.summary.ci_workflow_regression_reason_counts
  -> registry_release_readiness CI regression reason summary
```

## 测试覆盖

`tests/test_release_readiness_comparison.py` 新增 archived path regression 用例：

- baseline readiness 仍为 `ready`。
- current readiness 仍为 `ready`。
- 只有 `ci_workflow_archived_path_portability_check_ready` 从 `True` 变成 `False`。
- comparison 应输出：
  - `ci_workflow_regression_count=1`
  - `ci_workflow_archived_path_portability_check_ready_changed_count=1`
  - `ci_workflow_archived_path_portability_check_ready_regression_count=1`
  - reason 为 `archived_path_portability_check_not_ready`

artifact 测试同步检查 CSV、Markdown、HTML 是否出现 archived path 字段。

聚焦测试命令：

```powershell
python -m pytest tests/test_release_readiness_comparison.py tests/test_registry_rankings.py tests/test_registry.py -q -o cache_dir=runs/pytest-cache-v465-focused
```

结果：`40 passed`。

## 运行证据

运行证据归档在 `d/465`：

- `d/465/解释/source-inputs/v464-baseline-archived-ready/release_readiness.json`
- `d/465/解释/source-inputs/v465-current-archived-regressed/release_readiness.json`
- `d/465/解释/release-readiness-comparison-archived-path/release_readiness_comparison.json`
- `d/465/解释/release-readiness-comparison-archived-path/release_readiness_deltas.csv`
- `d/465/解释/release-readiness-comparison-archived-path/playwright_snapshot.md`
- `d/465/图片/release-readiness-comparison-archived-path.png`

这些产物是本版最终证据，不是临时 fixture。后续可以直接用 JSON 或 CSV 复核 archived path readiness regression。

## 一句话总结

v465 让 archived path portability readiness 进入跨版本比较和 registry CI regression reason 链路，补齐了从 CI gate 到发布对比的闭环。

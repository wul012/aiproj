# v380 release readiness drift smoke comparison 代码讲解

## 本版目标和边界

v380 的目标是把 v379 暴露出来的 `ci_workflow_release_readiness_drift_contract_smoke_ready` 纳入 release readiness comparison。

v379 已经让单个 release readiness dashboard 能看到 drift-contract smoke 是否 ready。v380 解决的是多版本对比问题：如果 baseline 是 ready，而 candidate 变成 not ready，即使整体 `ci_workflow_status` 仍然是 `pass`、failed check 仍然是 `0`，comparison 也要把它标成 CI workflow regression。

本版不新增 CI step，不新建 registry/maturity 传播链，不改变 release readiness dashboard 的生成规则，也不把 smoke ready 当作模型质量证明。

## 前置能力

本版承接 v377-v379：

- v377 提供 release readiness drift contract checker。
- v378 把 checker 包成稳定 CI smoke。
- v379 把 smoke ready 状态透传到 CI hygiene、audit、release bundle 和 release readiness。

v380 的链路是：

```text
release_readiness.summary.ci_workflow_release_readiness_drift_contract_smoke_ready
        |
        v
release_readiness_comparison row
        |
        v
delta changed/regressed fields
        |
        v
CSV / Markdown / HTML / CLI
```

## 关键文件

### `src/minigpt/release_readiness_comparison.py`

`_row_from_report()` 新增行字段：

```text
ci_workflow_release_readiness_drift_contract_smoke_ready
```

这个字段来自每个 `release_readiness.json` 的 summary。它是对单个 release readiness dashboard 的只读采样，不重新计算 CI workflow。

`_delta_from_baseline()` 新增四个 delta 字段：

```text
baseline_ci_workflow_release_readiness_drift_contract_smoke_ready
compared_ci_workflow_release_readiness_drift_contract_smoke_ready
ci_workflow_release_readiness_drift_contract_smoke_ready_changed
ci_workflow_release_readiness_drift_contract_smoke_ready_regressed
```

其中 `regressed` 的规则是：

```text
baseline is True and compared is not True
```

这样旧版本缺字段不会误判成回归，只有明确从 ready 退化到 false/missing 才进入 CI regression。

`_summary()` 新增两个计数：

```text
ci_workflow_release_readiness_drift_contract_smoke_ready_changed_count
ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count
```

`_is_ci_workflow_regression()` 也消费新字段。它让 drift smoke ready 退化和 failed check 增加、order violation 增加、CI status 降级处在同一个 CI hygiene regression 桶里。

### `src/minigpt/release_readiness_comparison_artifacts.py`

CSV 行输出新增 drift smoke ready 列。delta CSV 新增 baseline/compared/changed/regressed 四列。

Markdown 和 HTML 做两件事：

- summary 展示 drift smoke ready change/regression count。
- matrix/delta 表格展示每个 release 的 ready 值和每个 candidate 的 changed/regressed 状态。

这些 artifact 是最终 release comparison 证据，可供后续人工 review 或其他模块读取。

### `scripts/compare_release_readiness.py`

CLI stdout 新增：

```text
ci_workflow_release_readiness_drift_contract_smoke_ready_changed_count=...
ci_workflow_release_readiness_drift_contract_smoke_ready_regression_count=...
```

CI log 或本地 shell 不需要打开 JSON，就能看到 drift smoke ready 是否发生退化。

## 测试覆盖

`tests/test_release_readiness_comparison.py` 更新了测试夹具，让默认 readiness report 带上 drift smoke ready。

新增测试覆盖一个关键场景：

```text
baseline: ci_workflow_status=pass, drift_smoke_ready=True
current:  ci_workflow_status=pass, drift_smoke_ready=False
```

断言重点：

- release readiness 总状态保持 `ready`。
- `ci_workflow_status_changed=False`。
- `ci_workflow_release_readiness_drift_contract_smoke_ready_changed=True`。
- `ci_workflow_release_readiness_drift_contract_smoke_ready_regressed=True`。
- `ci_workflow_regression_count=1`。
- recommendation 进入 CI workflow hygiene regression。

输出测试还断言 CSV、delta CSV、Markdown 和 HTML 都包含 drift smoke comparison 字段。

阶段验证：

```text
15 passed
```

最终全量验证：

```text
679 passed
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
d/380/图片/01-release-readiness-drift-smoke-comparison-evidence.png
d/380/解释/说明.md
```

证据页展示 comparison summary、delta regression、artifact columns 和验证结果。

## 一句话总结

v380 让 release readiness drift-contract smoke ready 从“单版可见”升级为“跨版本可比较、可判定退化”的 CI hygiene regression 证据。

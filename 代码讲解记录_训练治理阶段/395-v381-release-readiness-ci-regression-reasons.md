# v381 release readiness CI regression reasons 代码讲解

## 本版目标和边界

v381 的目标是让 release readiness comparison 不只告诉 reviewer “有 CI workflow regression”，还要说明 regression 的具体原因。

v380 已经能把 drift-contract smoke ready 从 `True` 退化到 `False/None` 判为 CI 回归。但 recommendation 仍然沿用旧提示，只让人检查 failed-check 和 order-violation delta。v381 把 CI 回归原因拆成机器可读 reason list 和 summary count，让输出、建议和真实回归类型对齐。

本版不新增新的治理链路，不改变 release readiness dashboard 输入格式，不向 registry/maturity 继续传播，也不改变 v380 对 drift smoke ready 的判定规则。

## 前置能力

本版承接 v379-v380：

- v379 让单个 release readiness dashboard 能看到 drift-contract smoke ready。
- v380 让 release readiness comparison 能比较这个 ready 状态并判定回归。

v381 的链路是：

```text
delta fields
   |
   v
_ci_workflow_regression_reasons()
   |
   v
delta.ci_workflow_regression_reasons
   |
   v
summary.ci_workflow_regression_reason_counts
   |
   v
CSV / Markdown / HTML / CLI / recommendation
```

## 关键文件

### `src/minigpt/release_readiness_comparison.py`

新增 `_ci_workflow_regression_reasons()`，集中判断 CI regression 原因：

```text
failed_checks_increased
order_violations_increased
drift_contract_smoke_not_ready
workflow_status_downgraded
```

原来的 `_is_ci_workflow_regression()` 改为读取 reason list：

```text
bool(_ci_workflow_regression_reasons(delta))
```

这样不会在多个函数里重复维护一套 CI 回归判断。

`_summary()` 新增：

```text
ci_workflow_regression_reasons
ci_workflow_regression_reason_counts
```

`_recommendations()` 会把 reason counts 写进建议，例如：

```text
drift-contract smoke readiness=1
```

`_delta_explanation()` 也会把 delta 级 reason 展开成人可读解释。

### `src/minigpt/release_readiness_comparison_artifacts.py`

delta CSV 新增：

```text
ci_workflow_regression_reasons
```

Markdown 和 HTML 输出新增两处：

- Summary 展示 `CI workflow regression reasons`。
- Delta 表展示每个 candidate 的 `CI regression reasons`。

这些输出是最终 comparison 证据，后续人工 review 不需要再从多个 delta 字段反推原因。

### `scripts/compare_release_readiness.py`

CLI stdout 新增：

```text
ci_workflow_regression_reason_counts={...}
```

本地 shell 和 CI log 可以直接看到 failed check、order violation、status downgrade、drift smoke ready 哪一类造成了 CI regression。

### `tests/test_release_readiness_comparison.py`

测试覆盖三类原因：

- failed checks 增加并伴随 workflow status downgrade。
- order violations 增加但 CI status 不变。
- drift-contract smoke ready 从 `True` 变 `False`，且 CI status 不变。

输出测试还断言 delta CSV、Markdown 和 HTML 都包含 reason 字段。

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
d/381/图片/01-release-readiness-ci-regression-reasons-evidence.png
d/381/解释/说明.md
```

证据页展示 reason counts、CLI stdout 和关键输出字段。

## 一句话总结

v381 让 release readiness comparison 的 CI 回归从“一个总数”升级为“有原因、有计数、能指导检查方向”的可审计证据。

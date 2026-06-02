# v778 release readiness comparison regression split

## 本版目标和边界

v778 是一次纯维护优化版本，不新增模型训练、评估、发布 gate 或新的 report schema。它延续 v777 对 `release_readiness_comparison.py` 的拆分，但这次处理的不是叙事文本，而是 regression 判定语义。

本版明确不改变：

- comparison report 的 JSON 字段。
- release readiness comparison 的 renderer。
- `tests/test_release_readiness_comparison.py` 保护的行为。
- `status_delta_label` 等已有公开导出。

## 为什么这一刀有必要

v777 后，主文件仍然承担三类职责：

- 构建 comparison row 和 baseline delta。
- 汇总 comparison summary。
- 判断 CI workflow、test coverage、benchmark history 是否回退。

第三类职责增长很快：每新增一个 CI 检查、一个 benchmark readiness 条件或一个 coverage 状态，都可能加入新的 score 表和 reason 逻辑。把它继续留在主文件里，会让主文件重新膨胀。因此 v778 把 regression 判定集中到新模块。

## 关键文件

### `src/minigpt/release_readiness_comparison_regressions.py`

新增模块，负责回答“某个 delta 是否构成回退，以及回退原因是什么”：

- `ci_workflow_regression_reasons(delta)`：根据 failed check、order violation、drift smoke、archived path portability、receipt failure-smoke plan 等字段生成 CI regression reason。
- `is_ci_workflow_regression(delta)`：判断 CI workflow 是否有任一 regression reason。
- `is_test_coverage_regression(delta)`：根据 coverage percent、gap 和 coverage status score 判断测试覆盖是否退步。
- `has_benchmark_history_delta(delta)`：判断 benchmark history 是否存在任意变化。
- `is_benchmark_history_regression(delta)`：判断 benchmark history 是否出现回退，包括 status 降级、fail reason 新增、exit code 变差、ready count 下降等。
- `benchmark_history_status_score(value)`、`max_abs_delta(deltas, key)` 等 score/helper 函数也集中在这里。

这个模块只消费 delta，不读取文件，不写 artifact，不关心 HTML/Markdown 输出。

### `src/minigpt/release_readiness_comparison.py`

主文件现在通过别名导入 regression helper：

```python
from minigpt.release_readiness_comparison_regressions import (
    benchmark_history_status_score as _benchmark_history_status_score,
    ci_workflow_regression_reasons as _ci_workflow_regression_reasons,
    has_benchmark_history_delta as _has_benchmark_history_delta,
    is_benchmark_history_regression as _is_benchmark_history_regression,
    is_ci_workflow_order_regression as _is_ci_workflow_order_regression,
    is_ci_workflow_regression as _is_ci_workflow_regression,
    is_test_coverage_regression as _is_test_coverage_regression,
    max_abs_delta as _max_abs_delta,
    positive_number as _positive_number,
)
```

这样 `_summary` 和 `_delta_from_baseline` 的调用形态保持稳定，但具体判定逻辑不再塞在主文件底部。

## 数据流

```text
comparison row
  -> _delta_from_baseline
  -> release_readiness_comparison_regressions.*
  -> delta regression reasons / summary regression counts
  -> comparison report
```

v778 的关键边界是：主文件生产 delta，regression 模块解释 delta 是否构成风险。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\release_readiness_comparison.py src\minigpt\release_readiness_comparison_regressions.py
python -m pytest tests\test_release_readiness_comparison.py -q -o cache_dir=runs\pytest-cache-v778-focused
```

结果 `20 passed`。这些测试覆盖 comparison summary、delta explanation、recommendation、renderer escaping 等行为，因此能确认拆分没有改变外部报告结果。

## 运行证据

本版运行证据归档在：

- `e/778/解释/说明.md`
- `e/778/解释/refactor-summary.html`
- `e/778/图片/v778-release-readiness-comparison-regression-split.png`

这些证据用于说明维护拆分的边界、行数变化和验证命令，不作为新的生产 contract。

## 一句话总结

v778 把 release readiness comparison 的回退判定从主链里抽出，让主文件连续两版从 767 行降到 457 行，并把后续 CI/coverage/benchmark 语义扩展放进更适合维护的位置。

# v777 release readiness comparison narrative split

## 本版目标和边界

v777 不做新的模型能力、训练管线或发布治理功能，而是一次面向可维护性的拆分。它处理的是 `release_readiness_comparison.py` 里长期混在一起的两类职责：

- 一类是可计算的比较事实：读取 readiness JSON、生成 row、对 baseline 计算 delta、汇总 regression count。
- 另一类是叙事层输出：解释某个 delta 为什么变化、把 CI regression reason 转成可读标签、根据 summary 给出 release handoff recommendation。

本版只移动第二类职责，不改变 report schema，不改变 JSON 字段，不改变 renderer，不改变 CLI 行为。

## 前置路线

这版延续 v773-v776 的维护路线：先拆 promoted seed receipt/review/comparison 的验证、输出和建议文本，再回到仍超过 700 行的 release readiness comparison。它不是“为了拆而拆”，而是把最容易继续膨胀的文字叙事层先抽出，避免后续新增 CI reason 或 benchmark readiness reason 时继续把主文件拉大。

## 关键文件

### `src/minigpt/release_readiness_comparison.py`

主文件现在保留比较主链：

- `build_release_readiness_comparison` 仍是入口。
- `_row_from_report` 负责把 readiness report 摊平成 comparison row。
- `_delta_from_baseline` 负责从 baseline 和 compared row 计算差异。
- `_summary` 负责统计 ready/review/blocked、CI workflow regression、coverage regression、benchmark history regression 等汇总指标。
- `_ci_workflow_regression_reasons` 仍在主文件里，因为它依赖 delta 的计算事实，后续可以单独继续拆成 regression helper 模块。

拆分后主文件从 767 行降到 605 行，职责更集中。

### `src/minigpt/release_readiness_comparison_narrative.py`

新增 narrative 模块承接解释和建议：

- `release_readiness_delta_explanation(delta)`：把 delta 字段组合成可读解释。
- `status_delta_label(value)`：保留 `+1` / `0` / `-1` 这类显示规则。
- `build_release_readiness_comparison_recommendations(summary, deltas)`：根据 summary 和 deltas 输出 release handoff 建议。
- `_ci_workflow_reason_label` / `_ci_workflow_reason_summary`：把内部 reason id 翻译成可读口径。

这里没有读取文件、没有写文件、没有重新计算 delta，只消费主文件已经产出的结构化事实。

## 数据流

```text
readiness JSON paths
  -> build_release_readiness_comparison
  -> _row_from_report
  -> _delta_from_baseline
  -> _summary
  -> release_readiness_delta_explanation / build_release_readiness_comparison_recommendations
  -> comparison report
```

v777 的关键点是最后一步由 narrative 模块负责。这样主链输出事实，narrative 只负责表达事实。

## 保持的兼容性

`status_delta_label` 仍然从 `release_readiness_comparison` 的 `__all__` 导出。实现位置变了，但调用方不需要改 import。

`_delta_explanation` 和 `_recommendations` 在主文件中通过别名导入：

```python
from minigpt.release_readiness_comparison_narrative import (
    build_release_readiness_comparison_recommendations as _recommendations,
    release_readiness_delta_explanation as _delta_explanation,
    status_delta_label,
)
```

这让内部调用点保持稳定，同时把真实实现转移出去。

## 测试覆盖

本版跑了 release readiness comparison 的定向测试：

```powershell
python -m py_compile src\minigpt\release_readiness_comparison.py src\minigpt\release_readiness_comparison_narrative.py
python -m pytest tests\test_release_readiness_comparison.py -q -o cache_dir=runs\pytest-cache-v777-focused
```

结果是 `20 passed`。这组测试覆盖了 comparison report 的主要字段、delta 解释、recommendation 分支和 renderer 转义路径，因此能保护拆分后 report 行为不漂移。

## 运行证据

本版运行证据归档在：

- `e/777/解释/说明.md`
- `e/777/解释/refactor-summary.html`
- `e/777/图片/v777-release-readiness-comparison-narrative-split.png`

HTML 证据不是下游消费 contract，只是本版拆分结果、行数和测试命令的可视化说明。

## 一句话总结

v777 把 release readiness comparison 的“事实计算”和“文字解释”分开，降低后续 CI regression、benchmark history 和 release handoff 口径继续演进时的维护成本。

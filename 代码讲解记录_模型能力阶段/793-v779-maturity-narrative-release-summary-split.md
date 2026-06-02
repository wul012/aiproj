# v779 maturity narrative release summary split

## 本版目标和边界

v779 是维护拆分版本，不新增模型训练、benchmark、release gate 或新的 artifact。它处理的是 `maturity_narrative_summary.py` 中的 release readiness context 归一化长块。

本版不改变：

- maturity narrative 的最终 JSON 字段。
- 现有 `build_maturity_narrative_summary` 调用入口。
- `build_maturity_narrative_recommendations` 和 warnings 的外部导出。
- 测试 fixture 和 report schema。

## 为什么这一刀有必要

`maturity_narrative_summary.py` 原本承担了太多角色：

- 汇总 maturity、registry、request history、benchmark scorecard、dataset card。
- 计算 portfolio status。
- 生成 recommendations 和 warnings。
- 把 `release_readiness_context` 与旧的 `maturity_summary` fallback 字段合并。

其中 release readiness context 归一化是最重的一块：它要处理 CI workflow regression、archived path portability、benchmark readiness requirement、failed reason drift、suite design delta 等大量字段。这个逻辑继续放在主文件中，会让后续 release-readiness 字段变化时牵动整个 maturity narrative。

## 关键文件

### `src/minigpt/maturity_narrative_release.py`

新增模块提供：

```python
build_maturity_narrative_release_summary(maturity_summary, release_context)
```

它负责把两类输入整理成统一 release summary：

- 新链路优先使用 `release_readiness_context`。
- 旧链路或历史报告则从 `maturity_summary` 中读取 fallback 字段。

它还保留原有行为：当 benchmark readiness requirement 状态变化、failed reason 新增/混合、suite design regression 等出现时，将 `trend_status` 归为 `benchmark-regressed`。

### `src/minigpt/maturity_narrative_summary.py`

主文件现在导入：

```python
from minigpt.maturity_narrative_release import build_maturity_narrative_release_summary as _release_summary
```

主文件保留组合层职责：

- 读取并汇总 scorecard、decision、history、dataset rows。
- 计算 portfolio status。
- 生成 recommendations 和 warnings。
- 输出最终 summary 字典。

拆分后，主文件从 715 行降到 534 行。

## 数据流

```text
maturity summary + release_readiness_context
  -> build_maturity_narrative_release_summary
  -> normalized release summary
  -> build_maturity_narrative_summary
  -> portfolio status / recommendations / final narrative summary
```

这说明 release 模块只做输入归一化，不负责最终叙事展示。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\maturity_narrative_summary.py src\minigpt\maturity_narrative_release.py
python -m pytest tests\test_maturity_narrative.py -q -o cache_dir=runs\pytest-cache-v779-focused
```

结果 `20 passed`。这组测试覆盖 maturity narrative 的主入口、summary 字段、recommendations、warnings 和 builder 接线，因此能确认拆分后的 release summary fallback 行为没有漂移。

## 运行证据

本版运行证据归档在：

- `e/779/解释/说明.md`
- `e/779/解释/refactor-summary.html`
- `e/779/图片/v779-maturity-narrative-release-summary-split.png`

这些文件用于证明拆分范围、行数变化和定向测试结果。

## 一句话总结

v779 把 maturity narrative 中最重的 release context 归一化逻辑拆成独立模块，让主 summary 文件更适合继续承接 portfolio 级别的汇总编排。

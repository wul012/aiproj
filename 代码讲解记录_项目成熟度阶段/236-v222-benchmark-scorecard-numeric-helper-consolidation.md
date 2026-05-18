# v222 benchmark scorecard numeric helper consolidation 代码讲解

## 本版目标

v222 的目标是把 benchmark scorecard 链路里的重复数值转换 helper 接入 `report_utils`。

v221 已经新增：

```text
number_or_none()
number_or_default()
```

并完成训练运行证据与 training scale gate 的首批迁移。v222 继续处理同类问题，但范围限定在 benchmark scorecard 评估链。

## 不做什么

本版不改变 benchmark scorecard 的评分规则。

本版不改变 comparison delta、promotion decision、Markdown/HTML artifact 的字段结构。

本版也不继续扩展功能。它是一版质量收口：减少重复转换逻辑，让后续评估链维护更稳。

## 前置路线

本版承接：

```text
v195 utc_now 收敛
v196 benchmark scorecard dict/list helper 收敛
v197 benchmark scorecard artifact helper 收敛
v221 numeric helper 首批收敛
v222 benchmark scorecard numeric helper 收敛
```

这条路线说明项目正在把高频、低风险、语义稳定的 helper 逐步统一到 `report_utils`。

## `src/minigpt/benchmark_scorecard.py`

`benchmark_scorecard.py` 中的 `_number()` 用于把 pair batch 的 `case_count` 等字段转成可比较数值。

本版改为：

```python
def _number(value: Any) -> float | None:
    number = number_or_none(value, float)
    return float(number) if number is not None else None
```

局部 `_number()` 仍然存在，因为它表达 scorecard builder 自己的业务意图：这里需要的是 `float | None`。

## `src/minigpt/benchmark_scorecard_scoring.py`

scoring 模块里的 `_number()` 服务于 rubric、字符数、flag count 等评分输入。

本版让它复用 `number_or_none()`，但不改变 `_round_optional()`、rubric check、case score 的输出结构。

这保护了一个重要边界：scorecard 的“缺失指标”仍然是 `None`，不会被误转成 0。

## `src/minigpt/benchmark_scorecard_comparison_helpers.py`

comparison helper 里的 `_number()` 用于 case delta 和 relation 判断。

迁移后，delta 计算仍然保持原规则：

```text
无法转换 -> None
两边都有数值 -> 计算 delta
缺少任一边 -> delta 为 None
```

这对 benchmark comparison 很重要，因为缺失数据不能被伪装成 0 分。

## `src/minigpt/benchmark_scorecard_decision.py`

decision 模块同时存在三类转换：

```text
_number() -> float | None
_int() -> int，失败时 0
_int_or_none() -> int | None
```

本版分别接入：

```text
_number()      -> number_or_none(value, float)
_int()         -> number_or_default(value, 0, int)
_int_or_none() -> number_or_none(value, int)
```

这样 promotion decision 仍然保留保守默认：某些计数无法读取时按 0 处理；而可选字段仍然保留 `None`。

## 输入输出

输入仍然来自 eval suite、generation quality、pair batch、scorecard comparison 和 decision summary。

输出没有 schema 变化：

```text
scorecard cases
scorecard summaries
comparison case deltas
promotion decision evaluations/recommendations
```

改变的只是内部转换规则的来源，从局部重复代码变成共享 helper。

## 测试覆盖

本版聚焦运行：

```text
tests.test_benchmark_scorecard
tests.test_benchmark_scorecard_comparison
tests.test_benchmark_scorecard_decision
tests.test_report_utils
```

这些测试覆盖 scorecard 构建、scorecard comparison、promotion decision 以及公共 helper 基础语义。

全量 unittest discovery 也会一起运行，确认这次 helper 迁移没有影响其他治理链路。

## 运行证据

本版运行证据归档在 `c/222`：

- `图片/01-benchmark-scorecard-numeric-helper-tests.png`
- `图片/02-benchmark-scorecard-helper-scan.png`
- `图片/03-benchmark-scorecard-numeric-helper-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、源码迁移点可见、转换语义 smoke 正确、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v222 不把模型变强，也不新增评估指标。

它让 benchmark scorecard 评估链的基础转换规则更集中，避免 scoring、comparison、decision 各自复制相似逻辑。对后续更严格的 benchmark 和真实 checkpoint 对比来说，这是维护可靠性的地基。

## 一句话总结

v222 把数值 helper 收敛推进到 benchmark scorecard 评分、比较和决策层，让评估链共享公共转换规则，同时保留缺失值与默认值的语义边界。

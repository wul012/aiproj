# v223 generation quality numeric helper consolidation 代码讲解

## 本版目标

v223 的目标是把 generation-quality 链路里的重复 `_number()` helper 接入 `report_utils.number_or_none()`。

v221 先建立公共数值转换 helper，v222 把它带到 benchmark scorecard 评分、比较和决策层。v223 继续处理同类问题，但范围限定在 generation-quality 分析和 artifact 渲染两个模块。

## 不做什么

本版不改变生成质量检查规则。

本版不改变 `low_diversity`、`empty_continuation`、`repeated_ngram` 等 flag 判定。

本版也不改变 JSON、CSV、Markdown、SVG 或 HTML 输出结构。

## 前置路线

本版承接：

```text
v221 numeric helper 首批收敛
v222 benchmark scorecard numeric helper 收敛
v223 generation quality numeric helper 收敛
```

这条路线逐步把评估链路里的重复转换逻辑收到 `report_utils`，但仍然保留每个模块的局部适配函数来表达业务语义。

## `src/minigpt/generation_quality.py`

分析模块里的 `_number()` 用于：

```text
_round_avg()
_ratio_label()
```

本版改为：

```python
def _number(value: Any) -> float | None:
    number = number_or_none(value, float)
    return float(number) if number is not None else None
```

这保持了原来的语义：

```text
None / "" / bad value -> None
可转换数值 -> float
```

因此平均值计算仍然跳过缺失值，ratio label 仍然把缺失值显示为 `missing`。

## `src/minigpt/generation_quality_artifacts.py`

artifact 模块里的 `_number()` 用于 Markdown/HTML/SVG 中的比例展示。

迁移后，artifact 渲染仍然保持：

```text
缺失 ratio -> missing
有效 ratio -> 百分比标签
```

这说明本版没有改变证据展示，只减少了重复转换代码。

## 输入输出

输入仍然是 eval suite / generation outputs 中的 case metrics。

输出仍然是：

```text
generation_quality.json
generation_quality.csv
generation_quality.md
generation_quality.svg
generation_quality.html
```

字段、状态、flag、summary 均不变。

## 测试覆盖

本版聚焦运行：

```text
tests.test_generation_quality
tests.test_report_utils
```

这些测试覆盖 generation-quality report 构建、artifact 输出和公共 helper 基础语义。

全量 unittest discovery 也会运行，确认这次迁移没有影响其他项目治理链路。

## 运行证据

本版运行证据归档在 `c/223`：

- `图片/01-generation-quality-numeric-helper-tests.png`
- `图片/02-generation-quality-helper-scan.png`
- `图片/03-generation-quality-numeric-helper-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、源码迁移点可见、转换语义 smoke 正确、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v223 不新增模型能力，也不新增生成质量指标。

它让 generation-quality 证据链的基础转换规则更集中，减少分析层和展示层各自复制 `_number()` 的维护成本。

## 一句话总结

v223 把公共数值 helper 推进到 generation-quality 分析与 artifact 渲染，让生成质量证据继续保持同一套转换语义。

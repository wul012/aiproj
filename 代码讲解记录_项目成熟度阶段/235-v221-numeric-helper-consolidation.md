# v221 numeric helper consolidation 代码讲解

## 本版目标

v221 的目标是把重复出现的数值转换 helper 收敛到 `report_utils`。

这次优化来自一次质量诊断：项目中多个模块存在局部 `_int()` / `_float()`，语义接近但散落在不同文件里。它们不是严重 bug，但会增加后续维护成本：以后如果要统一处理空字符串、`None`、布尔值或非法输入，就需要逐个模块确认。

## 不做什么

本版不处理长文件名，也不把所有 TypedDict/Literal 定义集中化。

本版也不抽象 30 多个 artifact writer。那些属于中期结构治理，改动面更大。v221 只处理“数值转换 helper 重复”这一条明确、低风险、可测试的优化项。

## 前置路线

本版承接 v195-v197 的 report-utils 收敛路线：

```text
v195 utc_now 收敛
v196 dict/list helper 收敛
v197 artifact helper 收敛
v221 numeric helper 收敛
```

这条路线的共同原则是：先把稳定、小而通用的 helper 放进 `report_utils`，再让具体业务模块保留自己的语义适配层。

## `src/minigpt/report_utils.py`

### `number_or_none()`

新增公共 helper：

```python
def number_or_none(value: Any, number_type: type[int] | type[float] = float) -> int | float | None:
```

它表达的是“无法转换就返回 `None`”：

```text
None -> None
"" -> None
True/False -> None
"3" + int -> 3
"2.5" + float -> 2.5
bad value -> None
```

这里特意把 bool 排除掉，因为 Python 里 `int(True) == 1`。在报告和证据链里，把布尔值默默转成 0/1 容易掩盖输入字段错误。

### `number_or_default()`

新增公共 helper：

```python
def number_or_default(value: Any, default: int | float = 0, number_type: type[int] | type[float] = float) -> int | float:
```

它建立在 `number_or_none()` 上：

```text
能转换 -> 返回转换后的数值
不能转换 -> 返回调用方给定 default
```

这让调用方可以清楚表达两类不同语义：

- 缺失值应该保留为 `None`
- 缺失值应该降级为默认数值

## `src/minigpt/training_run_evidence_components.py`

训练运行证据组件里的 `_int()` / `_float()` 原本返回 `int | None` / `float | None`。

这个语义不能简单换成默认 0，因为证据报告里“没有数据”和“数值为 0”是两回事。

因此本版保留局部适配函数：

```python
def _int(value: Any) -> int | None:
    number = number_or_none(value, int)
    return int(number) if number is not None else None
```

局部函数继续承担业务语义，公共 helper 只负责底层转换规则。

## `src/minigpt/training_scale_gate.py`

training scale gate 里的 `_int()` / `_float()` 原本在转换失败时返回 `0` / `0.0`。

这个语义也要保留，因为 gate 逻辑里缺失指标会被当作“不满足阈值”的保守默认值。

因此本版改成：

```python
def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))
```

这样 gate 仍然保守，同时和训练运行证据组件共享同一套底层转换规则。

## `tests/test_report_utils.py`

新增测试覆盖：

```text
number_or_none("3", int) == 3
number_or_none("2.5") == 2.5
number_or_none("") is None
number_or_none(None) is None
number_or_none(True, int) is None
number_or_default("bad", 7, int) == 7
number_or_default("4.5", 0.0) == 4.5
```

这些断言保护的是“公共 helper 的基础语义”。聚焦测试还一起运行 training run evidence 和 training scale gate 测试，确认迁移后的调用方行为没有被破坏。

## 输入输出

输入仍然是各报告模块从 JSON、CSV、metrics 或 manifest 中读取到的任意值。

输出分两类：

```text
number_or_none -> int / float / None
number_or_default -> int / float / default
```

没有新增 JSON 字段，没有改变 artifact schema，也没有改变 CLI 参数。

## 运行证据

本版运行证据归档在 `c/221`：

- `图片/01-numeric-helper-focused-tests.png`
- `图片/02-numeric-helper-source-scan.png`
- `图片/03-numeric-helper-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、源码迁移点可见、转换语义 smoke 正确、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v221 不提升模型能力，也不新增训练治理功能。

它的作用是降低证据链维护成本：后续更多报告模块如果要处理数值字段，可以复用 `report_utils` 的转换规则，再用局部函数表达自己的业务语义。

## 一句话总结

v221 把训练证据链里的数值转换从局部重复推进到公共 helper，并保留 `None` 与默认值两种关键语义边界。

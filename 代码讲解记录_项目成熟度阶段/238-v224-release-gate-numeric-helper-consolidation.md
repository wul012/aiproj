# v224 release gate numeric helper consolidation 代码讲解

## 本版目标

v224 的目标是把 release-gate 链路里的重复数值转换 helper 接入 `report_utils`。

前几版已经完成：

```text
v221 training evidence / gate numeric helper
v222 benchmark scorecard numeric helper
v223 generation quality numeric helper
```

v224 继续处理同类问题，但范围限定在 release gate policy 与 artifact 渲染。

## 不做什么

本版不改变 release gate profiles。

本版不改变 `standard`、`review`、`strict`、`legacy` 的阈值含义。

本版也不改变 release gate JSON/Markdown/HTML 输出结构。

## `src/minigpt/release_gate.py`

release gate policy 里有两类转换：

```text
_number()  -> float | None
_integer() -> int，失败时 0
```

本版分别接入：

```python
number_or_none(value, float)
number_or_default(value, 0, int)
```

这样保留原有语义：

- audit score 缺失时仍然是 `None`，score label 显示 `missing`
- ready run count 等整数无法读取时仍然保守归零

## `src/minigpt/release_gate_artifacts.py`

artifact 模块里的 `_number()` 用于输出层 score label。

迁移后，Markdown/HTML 仍然保持：

```text
缺失分数 -> missing
有效分数 -> 百分比标签
```

因此本版只减少重复转换代码，不改变读者看到的 release gate 证据。

## 输入输出

输入仍然是 release bundle 和 project audit / registry / request-history / generation-quality 等上游证据。

输出仍然是：

```text
release_gate.json
release_gate.md
release_gate.html
```

字段、状态、推荐语和 profile policy 均不变。

## 测试覆盖

本版聚焦运行：

```text
tests.test_release_gate
tests.test_release_gate_comparison
tests.test_report_utils
```

这些测试覆盖 release gate 构建、profile comparison、artifact facade 和公共 helper 基础语义。

全量 unittest discovery 也会运行，确认这次迁移没有影响其他项目治理链路。

## 运行证据

本版运行证据归档在 `c/224`：

- `图片/01-release-gate-numeric-helper-tests.png`
- `图片/02-release-gate-helper-scan.png`
- `图片/03-release-gate-numeric-helper-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、源码迁移点可见、转换语义 smoke 正确、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v224 不提升模型能力，也不新增发布规则。

它让 release gate 证据链的基础转换规则更集中，减少 policy 层和展示层各自复制 `_number()` 的维护成本。

## 一句话总结

v224 把公共数值 helper 推进到 release-gate policy 与 artifact 渲染，让发布闸门证据继续保持同一套转换语义。

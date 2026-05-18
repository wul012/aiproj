# v225 training scale run numeric helper consolidation 代码讲解

## 本版目标

v225 的目标是把 training-scale run 和 promotion 链路里的重复 `_int()` helper 接入 `report_utils.number_or_default()`。

前几版已经把 `number_or_none()` / `number_or_default()` 建成公共底座，并依次带入 training evidence、benchmark scorecard、generation quality、release gate。v225 继续推进，但只覆盖训练规模的 run/comparison/index/promotion 这一组同语义模块。

## 不做什么

本版不改变 suite consistency 判定。

本版不改变 promoted / review / blocked 状态。

本版也不改变 comparison、index、decision 的 JSON、CSV、Markdown、HTML 输出结构。

## `src/minigpt/training_scale_run_decision.py`

run decision 里的 `_int()` 用于推荐语、计数和 summary 读取。

本版改成：

```python
def _int(value: Any) -> int:
    return int(number_or_default(value, 0, int))
```

这保留了“读不到就按 0 处理”的保守策略。

## `src/minigpt/training_scale_run_comparison.py`

run comparison 里的 `_int()` 用于 summary 和比较派生值。

迁移后，比较结果的默认值语义不变，只是把转换规则集中到 `report_utils`。

## `src/minigpt/training_scale_promotion_index_helpers.py`

promotion index helper 里的 `_int()` 负责把 ready/promoted/blocked 等计数整合进推荐语。

本版让它复用 `number_or_default()`，避免和其他 run-level helper 各写一套失败归零逻辑。

## `src/minigpt/promoted_training_scale_comparison.py`

promoted comparison 里的 `_int()` 用于 summary 和手动校验计数。

这部分保留原语义：

```text
失败或缺失 -> 0
可读取 -> int
```

## `src/minigpt/promoted_training_scale_decision.py`

promoted decision 里的 `_int()` 用于 selected run / comparison summary / recommendation 计数。

迁移后，决策逻辑和推荐语没有变化，只是底层数值转换更统一。

## 输入输出

输入仍然是 training-scale run comparison、promotion index、promoted comparison 和 promoted decision 的 summary / rows / recommendations。

输出没有 schema 变化，只是内部 `_int()` 统一复用了 `report_utils.number_or_default()`。

## 测试覆盖

本版聚焦运行：

```text
tests.test_training_scale_run_decision
tests.test_training_scale_run_comparison
tests.test_training_scale_promotion_index
tests.test_promoted_training_scale_comparison
tests.test_promoted_training_scale_decision
tests.test_report_utils
```

这些测试覆盖训练规模 run/comparison/index/promotion 链路和公共 helper 基础语义。

全量 unittest discovery 也会运行，确认这次迁移没有影响其他项目治理链路。

## 运行证据

本版运行证据归档在 `c/225`：

- `图片/01-training-scale-run-numeric-helper-tests.png`
- `图片/02-training-scale-run-helper-scan.png`
- `图片/03-training-scale-run-numeric-helper-smoke.png`
- `图片/04-source-encoding-smoke.png`
- `图片/05-full-unittest.png`
- `图片/06-docs-check.png`

这些截图分别证明：聚焦测试通过、源码迁移点可见、转换语义 smoke 正确、source encoding 干净、全量测试通过、README/归档/讲解和源码关键词对齐。

## 证据链角色

v225 不新增训练能力，也不改晋级策略。

它把 training-scale 这一条 run-to-promote 证据链里的默认归零规则收束到公共 helper，减少后续重复维护成本。

## 一句话总结

v225 把默认归零 helper 推进到 training-scale run / comparison / promotion 链路，让训练规模晋级证据链继续共享统一转换规则。

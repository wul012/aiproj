# v782 promoted comparison summary split

## 本版目标和边界

v782 是维护拆分版本，不新增训练规模比较能力，不改变 promoted comparison 的 report schema，也不改变推荐文本。v775 已经把 recommendation 文本抽走，本版继续处理剩下的大块职责：summary 聚合。

本版不改变：

- `build_promoted_training_scale_comparison` 的函数签名。
- `promotions`、`comparison_inputs`、`summary`、`blockers`、`recommendations` 的输出结构。
- promoted comparison renderer。
- clean-batch guard 的具体判定。

## 为什么这一刀有必要

`promoted_training_scale_comparison.py` 原本剩下两类大职责：

- 读取 promotion index，筛选可比较 run，执行 `build_training_scale_run_comparison`。
- 统计一大批 handoff clean-batch、CI regression、suite mismatch、comparison-ready 字段。

第二类 summary 聚合超过 200 行，且字段密度很高。如果继续放在主文件里，后续新增 handoff 指标或 CI reason count 时会让比较执行逻辑越来越难读。

## 关键文件

### `src/minigpt/promoted_training_scale_comparison_summary.py`

新增模块提供：

```python
build_promoted_training_scale_comparison_summary(
    index_summary,
    promotions,
    comparison_inputs,
    comparison_report,
    comparison_status,
    blocked_reason,
)
```

它负责聚合：

- promotion 和 comparison-ready 数量。
- baseline、best_by_readiness、suite consistency。
- handoff suite consistency 和 mismatch totals。
- clean batch review count / unclean count。
- batch maturity CI regression count 和 reason counts。
- suite-design regression names。
- selected batch review/blocker/action totals。
- comparison blocked reason。

这个模块只消费已经归一化的 `promotions` 和 comparison report，不读取文件、不执行比较、不决定哪些 run 可以比较。

### `src/minigpt/promoted_training_scale_comparison.py`

主文件现在导入：

```python
from minigpt.promoted_training_scale_comparison_summary import (
    build_promoted_training_scale_comparison_summary as _summary,
)
```

主文件保留：

- `load_training_scale_promotion_index`
- `_promotion_rows`
- `_comparison_inputs`
- `_merge_comparison_rows`
- `_blockers`
- `_comparison_exclusion_reasons`
- `_clean_batch_review_guard`

拆分后主文件从 661 行降到 420 行。

## 数据流

```text
promotion index
  -> promotion rows
  -> comparison inputs
  -> training scale run comparison
  -> build_promoted_training_scale_comparison_summary
  -> promoted comparison report
```

v782 的边界是：主文件产出比较事实，summary 模块聚合这些事实。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\promoted_training_scale_comparison.py src\minigpt\promoted_training_scale_comparison_summary.py
python -m pytest tests\test_promoted_training_scale_comparison.py -q -o cache_dir=runs\pytest-cache-v782-focused
```

结果 `13 passed`。这些测试覆盖 promoted comparison 的 blockers、clean batch guard、summary 字段和 renderer escaping，能确认 summary 拆分没有改变 report 行为。

## 运行证据

本版运行证据归档在：

- `e/782/解释/说明.md`
- `e/782/解释/refactor-summary.html`
- `e/782/图片/v782-promoted-comparison-summary-split.png`

这些证据用于记录拆分边界、行数变化和定向测试结果。

## 一句话总结

v782 把 promoted comparison 的 summary 聚合从执行主链中拆出，让主模块回到 promotion index、比较输入和执行编排职责。

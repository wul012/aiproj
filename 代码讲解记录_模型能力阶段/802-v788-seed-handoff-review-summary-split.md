# v788 seed handoff review summary split

## 本版目标和边界

v788 是维护拆分版本，不新增 promoted seed handoff review 功能，不改变 summary 字段，不改变 requirement 判断，也不改变 automation gate 的返回结构。本版只把两个长 summary builder 从 `promoted_training_scale_seed_handoff_review.py` 拆到独立模块。

本版不改变：

- `build_seed_handoff_batch_review_summary` 的函数名。
- `build_seed_handoff_clean_batch_review_summary` 的函数名。
- 从 `promoted_training_scale_seed_handoff_review` 导入这两个函数的兼容路径。
- TypedDict 类型、requirement status domain、automation gate 和 suite alignment。

## 为什么这一刀有必要

`promoted_training_scale_seed_handoff_review.py` 原来同时包含：

- 两个长 summary builder：从 `handoff_batch_review` 和 `handoff_clean_batch_review` 中归一化大量字段。
- clean evidence requirement。
- clean batch review requirement。
- automation gate 和 automation summary。
- suite alignment 与 clean evidence readiness。

summary builder 的职责是“把上游字段铺平”，而 requirement/gate 的职责是“根据 summary 判断是否能继续”。两者放在一起会让 review 主模块显得很宽，尤其 clean batch summary 有大量 CI regression reason counts、boundary plan check、suite-design regression names 字段。

v788 把这两个长 summary builder 移到 `promoted_training_scale_seed_handoff_review_summary.py`，让主模块更集中处理 review 决策。

## 关键文件

### `src/minigpt/promoted_training_scale_seed_handoff_review_summary.py`

新增模块承接：

- `build_seed_handoff_batch_review_summary(baseline)`
- `build_seed_handoff_clean_batch_review_summary(baseline)`

它只做字段归一化，不判断 automation gate，不生成最终 handoff report，也不写文件。

### `src/minigpt/promoted_training_scale_seed_handoff_review.py`

主模块现在导入并 re-export summary builder：

```python
from minigpt.promoted_training_scale_seed_handoff_review_summary import (
    build_seed_handoff_batch_review_summary,
    build_seed_handoff_clean_batch_review_summary,
)
```

拆分后该文件从 613 行降到 410 行，主要保留类型定义、requirement 和 automation gate。

## 数据流

```text
selected baseline
  -> seed_handoff_review_summary builders
       -> batch review summary
       -> clean batch review summary
  -> seed_handoff_review requirements
       -> clean evidence requirement
       -> clean batch review requirement
  -> automation gate
  -> automation summary
```

v788 的关键边界是：summary builder 只归一化字段，requirement/gate 才做是否通过的判断。

## 测试覆盖

本版运行：

```powershell
python -m py_compile src\minigpt\promoted_training_scale_seed_handoff_review.py src\minigpt\promoted_training_scale_seed_handoff_review_summary.py
python -m pytest tests\test_promoted_training_scale_seed_handoff_review.py tests\test_promoted_training_scale_seed_review.py tests\test_promoted_training_scale_decision_review.py -q -o cache_dir=runs\pytest-cache-v788-focused
python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-v788
git diff --check
```

结果：

- focused tests: `11 passed`
- source encoding: `status=pass`
- diff check: pass

这些测试覆盖 batch review summary、clean batch review summary、boundary plan detail 优先级、suite alignment、seed review fallback 和 decision review handoff summary 消费。它们保护了拆分后字段语义不变。

## 运行证据

本版运行证据归档在：

- `e/788/解释/说明.md`
- `e/788/解释/refactor-summary.html`
- `e/788/图片/v788-seed-handoff-review-summary-split.png`

HTML 证据页展示了拆分后的职责边界、行数变化和测试结果。截图用于确认归档页可打开，核心指标可见。

## 一句话总结

v788 把 promoted seed handoff review 的长 summary 归一化层拆出，让 review 主模块聚焦 requirement 和 automation gate，也完成本轮十六版维护拆分收束。

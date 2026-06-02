# v774 handoff review recommendations split 代码讲解

## 本版目标和边界

v774 是维护性拆分路线第二版。目标是拆分 `promoted_training_scale_seed_handoff_review.py` 的 recommendation 区块，让主文件更专注于构建 review 数据结构。

本版不改变 seed handoff review 行为，不改变输出字段，不改变公共导入路径。

## 为什么拆 recommendations

`promoted_training_scale_seed_handoff_review.py` 原本 779 行，混合了两类职责：

- 结构化 summary/requirement/gate/automation/suite alignment 构建。
- 面向人的 review recommendation 文案生成。

后者包含大量条件分支和长文案，阅读时会打断核心数据流。把它抽走后，主文件更容易定位 gate 和 requirement 逻辑。

## 关键新增文件

- `src/minigpt/promoted_training_scale_seed_handoff_review_recommendations.py`
  - `build_seed_handoff_review_recommendations()`
  - `clean_batch_review_requirement_detail()`
  - clean evidence、clean batch review、handoff batch review、suite alignment 的私有 recommendation helper。

## 主文件变化

- `src/minigpt/promoted_training_scale_seed_handoff_review.py`
  - 从 recommendations 模块导入 `build_seed_handoff_review_recommendations`。
  - 用 alias 导入 `clean_batch_review_requirement_detail`，保持原来的 `_clean_batch_review_requirement_detail()` 调用点稳定。
  - 删除内联 recommendation helper。

行数变化：

```text
779 -> 613
```

## 契约保护

公共导入路径保持不变：

```python
from minigpt.promoted_training_scale_seed_handoff_review import build_seed_handoff_review_recommendations
```

这是因为主文件继续 re-export 该函数，并在 `__all__` 中保留原名称。

## 测试覆盖

验证命令：

```powershell
python -m pytest tests\test_promoted_training_scale_seed_handoff.py tests\test_promoted_training_scale_seed_handoff_review.py -q -o cache_dir=runs\pytest-cache-v774-focused
```

结果：

```text
33 passed
```

这些测试覆盖 recommendation 文案、clean batch review 边界、suite alignment 和 handoff 主流程，能证明拆分没有改变行为。

## 运行证据

- 归档说明：`e/774/解释/说明.md`
- HTML 摘要：`e/774/解释/refactor-summary.html`
- 截图：`e/774/图片/v774-handoff-review-recommendations-split.png`

一句话总结：v774 把 handoff review 的文案建议层拆出主流程，主文件从 779 行降到 613 行，维护边界更清楚。

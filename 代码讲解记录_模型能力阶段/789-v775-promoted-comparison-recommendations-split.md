# v775 promoted comparison recommendations split 代码讲解

## 本版目标和边界

v775 是维护性拆分路线第三版，目标是拆分 `promoted_training_scale_comparison.py` 的 recommendation 文案层。

本版不改变 promotion comparison 的输入、输出、summary 字段、CSV/HTML/Markdown 渲染，也不改变 comparison selection 逻辑。

## 为什么拆这里

`promoted_training_scale_comparison.py` 原本 777 行，核心职责已经不少：

- 加载 promotion index。
- 构造 promotion rows。
- 筛选 compare-ready inputs。
- 调用 training scale run comparison。
- 合并 comparison rows。
- 计算 summary。
- 生成 blockers。
- 生成 recommendations。
- 判断 clean-batch guard 和 comparison exclusion reasons。

recommendations 是长文本条件分支，和 comparison 数据构建不是同一层。拆出后主文件更像“数据构建器”，文案逻辑单独维护。

## 关键新增文件

- `src/minigpt/promoted_training_scale_comparison_recommendations.py`
  - `build_promoted_training_scale_comparison_recommendations()`
  - `_compared_recommendations()`
  - `_blocked_recommendations()`
  - `_append_visible_regression_notes()`

## 主文件变化

- `src/minigpt/promoted_training_scale_comparison.py`
  - 删除内联 `_recommendations()`。
  - 导入 `build_promoted_training_scale_comparison_recommendations as _recommendations`。

行数变化：

```text
777 -> 661
```

## 测试覆盖

验证命令：

```powershell
python -m pytest tests\test_promoted_training_scale_comparison.py -q -o cache_dir=runs\pytest-cache-v775-focused
```

结果：

```text
13 passed
```

这组测试覆盖 comparison blocked/compared 分支、clean batch review guard、HTML escaping 和输出写入，因此能保护 recommendation 拆分后的行为不变。

## 运行证据

- 归档说明：`e/775/解释/说明.md`
- HTML 摘要：`e/775/解释/refactor-summary.html`
- 截图：`e/775/图片/v775-promoted-comparison-recommendations-split.png`

一句话总结：v775 把 promoted comparison 的 recommendation 文案层拆成独立模块，主文件从 777 行降到 661 行。

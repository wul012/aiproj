# v632 required-term pair generation/internal alignment comparison

## 本版目标和边界

v632 新增 generation/internal alignment comparison。它不是新训练，也不是 promotion；它把已有 checkpoint 的两个证据面合并：

- generation replay：模型自由生成是否命中 fixed/loss。
- forced-choice internal：模型在固定候选下是否更偏向正确 term。

本版解决的问题是：v621 和 v630 都“看起来有价值”，但价值不在同一层，必须并表比较。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_generation_internal_alignment_comparison.py
src/minigpt/model_capability_required_term_pair_generation_internal_alignment_comparison_artifacts.py
scripts/run_model_capability_required_term_pair_generation_internal_alignment_comparison.py
tests/test_model_capability_required_term_pair_generation_internal_alignment_comparison.py
e/632/解释/model-capability-required-term-pair-generation-internal-alignment-comparison/
```

核心 builder 读取一组 source，每个 source 包含：

```text
label
refresh_report
forced_choice_report
refresh_path
forced_choice_path
```

然后输出每条路线的：

```text
generation_hit_terms
internal_expected_best_terms
generation_pair_full
internal_pair_full
alignment_class
```

## 核心判断

alignment class 负责把路线分成几类：

```text
generation_internal_pair_full
generation_pair_full_internal_partial
internal_pair_full_generation_gap
fixed_only_aligned_partial
loss_only_aligned_partial
partial_tradeoff
```

v632 的真实结果是：

```text
loss-internal-first-token  -> internal_pair_full_generation_gap
loss-internal-fixed-bridge -> fixed_only_aligned_partial
loss-internal-joint-cycle  -> generation_pair_full_internal_partial
```

## 运行结果

```text
decision=keep_generation_pair_full_and_repair_internal_preference
generation_pair_full_count=1
internal_pair_full_count=1
aligned_pair_full_count=0
best_source_labels=loss-internal-first-token,loss-internal-joint-cycle
```

这说明 v630 不能直接 promotion，但它比 v621 更接近可用生成效果；后续应以 v630 为主线修 internal preference。

## 测试覆盖

新增单测覆盖：

- generation pair-full + internal partial 时，决策进入 internal repair。
- internal pair-full + generation gap 时，决策进入 generation bridge。
- aligned pair-full 出现时优先选择 aligned candidate。
- JSON/CSV/text/Markdown/HTML 全格式输出。

## 一句话总结

v632 把“生成能不能出来”和“内部是否真偏好”分开量化，防止 v630 正结果被过早夸大。

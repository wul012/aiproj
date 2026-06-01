# v653 required-term pair alignment comparison with surface-first schedule

## 本版目标和边界

v653 的目标是把 v651/v652 的新结果放回既有 alignment comparison，不让一次新实验脱离历史矩阵单独判断。

本版不训练新模型，也不修改比较算法，只增加一个 source：`surface-first-schedule`。

## 输入

输入 source 包括：

- `loss-internal-first-token`
- `loss-internal-fixed-bridge`
- `loss-internal-joint-cycle`
- `loss-internal-balanced-anchor`
- `joint-cycle-internal-repair`
- `joint-cycle-light-merge`
- `surface-first-schedule`

每个 source 都由一个 refresh report 和一个 forced-choice report 组成。

## 核心结果

报告输出：

- `decision=keep_generation_pair_full_and_repair_internal_preference`
- `generation_pair_full_count=1`
- `internal_pair_full_count=2`
- `aligned_pair_full_count=0`

新增的 `surface-first-schedule` 被分类为：

- `generation_hit_terms=["fixed"]`
- `internal_expected_best_terms=["fixed"]`
- `alignment_class=fixed_only_aligned_partial`

这说明它没有成为生成候选，也没有成为内部锚点。

## 链路意义

v651/v652 单独看是“fixed-only 失败”。v653 的意义是把这个失败放进矩阵后判断它是否改变路线。结果是没有改变：

- 生成 pair-full 仍只来自 `loss-internal-joint-cycle`。
- 内部 pair-full 仍来自 `loss-internal-first-token` 和 `joint-cycle-internal-repair`。
- aligned pair-full 仍为 0。

## 运行证据

产物写入：

- `e/653/解释/model-capability-required-term-pair-alignment-comparison-with-surface-first-schedule/`
- `e/653/图片/v653-alignment-comparison-with-surface-first-schedule.png`

截图显示 Status=`pass`、Decision=`keep_generation_pair_full_and_repair_internal_preference`、Aligned full=`0`。

## 一句话总结

v653 把 surface-first schedule 纳入全矩阵，并确认它不是新主线，只是一个应记录的负向分支。

# v654 required-term pair route decision with surface-first schedule

## 本版目标和边界

v654 把 v653 的 full matrix 变成路线决策。它回答的问题是：加入 surface-first schedule 后，项目是否需要改变当前 generation route 或 internal anchor。

本版不改 route-decision 算法，不训练新模型，只消费 v653 的 comparison artifact。

## 输入输出

输入：

- `e/653/解释/model-capability-required-term-pair-alignment-comparison-with-surface-first-schedule/`

输出：

- `model_capability_required_term_pair_generation_internal_alignment_route_decision.json`
- CSV/TXT/Markdown/HTML 报告。
- Playwright 截图。

## 决策结果

报告显示：

- `decision=repair_internal_preference_preserve_generation_pair_full`
- `selected_generation_route=loss-internal-joint-cycle`
- `internal_anchor_route=joint-cycle-internal-repair`
- `direct_promotion_ready=False`

这说明 surface-first schedule 没有打破原先结论。

## 为什么不推进 surface-first

v651 生成侧只命中 `fixed`，v652 内部侧也只保 `fixed`。放进 v653 矩阵后，它被归类为 `fixed_only_aligned_partial`。

因此它不满足两类主线价值：

- 不是 generation pair-full。
- 不是 internal pair-full。

## 运行证据

产物写入：

- `e/654/解释/model-capability-required-term-pair-route-decision-with-surface-first-schedule/`
- `e/654/图片/v654-route-decision-with-surface-first-schedule.png`

截图显示 generation route 仍是 `loss-internal-joint-cycle`，internal anchor 仍是 `joint-cycle-internal-repair`。

## 一句话总结

v654 把 surface-first schedule 收束为负向探索，主线回到“保 v630 生成 pair-full，借 v640 内部锚点修偏好”。

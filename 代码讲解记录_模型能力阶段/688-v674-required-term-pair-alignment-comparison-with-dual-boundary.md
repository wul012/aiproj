# v674 required-term pair alignment comparison with dual-boundary

## 本版目标和边界

v674 的目标是把 v672/v673 的 explicit dual-boundary checkpoint 放回统一 alignment matrix，判断它是不是比历史路线更接近 required-term pair 的真实能力提升。

本版不训练新模型，不改 corpus，不做推广决策。它只比较已有 evidence：refresh/generation 报告和 forced-choice/internal 报告是否在同一个 source 上同时 pair-full。

## 前置链路

本版来自 v669-v673 的闭环：

- v669 诊断 constrained decode 仍缺 `fixed`，问题是 prefix fragment 不是完整 term。
- v670 规划 explicit dual-objective boundary。
- v671 注册 `equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair` corpus mode。
- v672 用该 corpus mode 训练 seed 3535，并观察到 generation pair-full。
- v673 对同一 checkpoint 做 forced-choice，确认内部偏好也完整匹配。

v674 的作用是把这条新路线与旧路线并排比较，避免只看单一新报告就过早乐观。

## 输入输出

输入由 6 组 source 组成，每组包含一个 refresh report 和一个 forced-choice report：

- `loss-internal-first-token`
- `loss-internal-joint-cycle`
- `joint-cycle-internal-repair`
- `v630-internal-repair-resume`
- `v630-light-merge-resume`
- `dual-boundary-seed-3535`

输出目录：

- `e/674/解释/model-capability-required-term-pair-alignment-comparison-with-dual-boundary/`

核心输出包括 JSON、CSV、text、Markdown 和 HTML。它们是对既有实验的只读汇总证据，后续 route decision 可以直接消费。

## 核心字段语义

- `generation_pair_full`: 自由生成是否同时命中 `fixed` 和 `loss`。
- `internal_pair_full`: forced-choice 内部评分是否同时偏好正确 term。
- `generation_internal_disagreement_terms`: 两层证据不一致的 term。
- `alignment_class`: 路线分类，例如 `generation_internal_pair_full`、`generation_pair_full_internal_partial` 或 `internal_pair_full_generation_gap`。
- `best_source_labels`: 当前矩阵中最优候选 source。

## 本版结果

v674 的汇总结果为：

- `generation_pair_full_count=2`
- `internal_pair_full_count=3`
- `aligned_pair_full_count=1`
- `best_source_labels=dual-boundary-seed-3535`
- `best_alignment_class=generation_internal_pair_full`

这说明历史路线虽然分别出现过生成正信号或内部正信号，但只有 dual-boundary seed 3535 同时满足两者。

## 测试与证据

测试运行：

```powershell
python -m pytest tests\test_model_capability_required_term_pair_generation_internal_alignment_comparison.py -q -o cache_dir=runs\pytest-cache-v674
```

测试保护的是 comparison renderer 和 source classification 的基本契约：只有 refresh/forced-choice 双报告一致时才进入 aligned pair-full。

运行证据：

- JSON/CSV/text/Markdown/HTML: `e/674/解释/model-capability-required-term-pair-alignment-comparison-with-dual-boundary/`
- 截图: `e/674/图片/v674-alignment-comparison-with-dual-boundary.png`
- 解释: `e/674/解释/说明.md`

一句话总结：v674 证明 explicit dual-boundary 当前是唯一同时通过 generation 和 internal 检查的候选，但仍需要多 seed 稳定性验证。

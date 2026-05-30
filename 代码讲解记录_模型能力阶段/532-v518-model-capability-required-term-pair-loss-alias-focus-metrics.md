# v518 required-term pair loss-alias focus metrics 代码讲解

## 本版目标与边界

v518 的目标是把 v517 的 normalized audit 发现接回主链路。v516 的 focus 报告只知道 strict hit，因此给出 no-repair；v517 只读审计发现这些 strict misses 在 normalization 后全部包含 `loss`。本版让 `loss-alias focus` builder 自己输出 strict 与 normalized 两套指标。

本版不训练更大的模型，不修改数据来源，也不把 normalized hit 当作 strict hit。它做的是指标补齐：让后续能力判断能同时看到“是否连续生成目标词”和“是否生成了被格式分隔的目标字符序列”。

## 前置链路

前置版本：

- v516：focused repair strict hit 为 0。
- v517：只读 normalized audit 发现 strict `0/4`，normalized `4/4`。

v518 复用 v516 的训练入口，但更新 focus builder 输出结构。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_metrics.py`
  - 新增共享 normalization helper。
  - 提供 `normalize_for_required_term()` 和 `required_term_hit_metrics()`。
- `src/minigpt/model_capability_required_term_pair_loss_alias_focus_components.py`
  - 拆出 case 选择、seed 清洗、预览、strict/metric decision 等纯 helper。
  - 避免 focus 主模块在加入双指标后继续膨胀。
- `src/minigpt/model_capability_required_term_pair_loss_alias_focus.py`
  - generation rows 增加 `strict_hit`、`normalized_hit`、`normalization_gain`、`normalized_continuation_preview`。
  - seed summary 增加 strict 与 normalized 计数。
  - top-level summary 增加 normalized full seed count 与 metric decision。
- `src/minigpt/model_capability_required_term_pair_loss_alias_focus_artifacts.py`
  - text/CSV/Markdown/HTML 输出 strict 与 normalized 指标。
- `src/minigpt/model_capability_required_term_pair_loss_alias_normalized_audit.py`
  - 改为复用共享 metrics helper，避免 normalization 规则分叉。
- `tests/test_model_capability_required_term_pair_loss_alias_focus.py`
  - 新增 split-loss fake generation，验证 strict miss 但 normalized full 的场景。

## 核心指标

新增行级字段：

- `strict_hit`
- `normalized_hit`
- `normalization_gain`
- `normalized_continuation_preview`

新增 seed 级字段：

- `focus_normalized_hit_case_count`
- `support_normalized_hit_case_count`
- `focus_normalized_full_coverage`
- `support_normalized_full_coverage`
- `normalization_gain_count`

新增 summary 字段：

- `loss_alias_focus_metric_decision`
- `focus_normalized_full_seed_count`
- `support_normalized_full_seed_count`
- `stable_focus_normalized_full_coverage`
- `stable_support_normalized_full_coverage`

这让报告能表达三层事实：

1. strict 是否成功。
2. normalized 是否显示隐藏信号。
3. normalized 信号是否足以改变下一步策略。

## 真实结果解释

v518 真实运行结果：

```text
loss_alias_focus_decision=loss_alias_focus_no_repair
loss_alias_focus_metric_decision=loss_alias_focus_strict_miss_normalized_support_full_signal
strict focus = 0/2
strict support = 0/4
normalized focus = 2/2
normalized support = 4/4
normalization_gain_count = 4
```

这个结果保留了 strict no-repair，同时说明模型确实输出了 `loss` 字符序列，只是被换行分隔。后续不应继续简单增加 repeat，而应把 strict/normalized 指标并列带入下一层评估或 decoding/path 分析。

## 测试覆盖

测试新增：

- fake strict full hit：strict 与 normalized 都 full，但 gain 为 0。
- fake empty：strict 与 normalized 都没有信号。
- fake split loss：strict miss，normalized full，decision 进入 `required_term_pair_loss_alias_focus_normalized_support_signal`。

这保护了一个关键边界：normalized signal 可以影响下一步建议，但不会伪装成 strict success。

## 运行证据

运行证据归档在：

```text
e/518/解释/model-capability-required-term-pair-loss-alias-focus-metrics/
e/518/图片/
```

截图：

```text
e/518/图片/01-model-capability-required-term-pair-loss-alias-focus-metrics.png
```

## 一句话总结

v518 把 loss-alias 评估从单一 strict hit 推进到 strict/normalized 双指标，避免继续用错误问题驱动训练。

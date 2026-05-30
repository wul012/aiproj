# v519 required-term pair loss-alias stability metrics 代码讲解

## 本版目标与边界

v519 的目标是把 v518 建立的 strict/normalized 双指标，从 focused repair 报告补回到上游 `loss-alias stability` 报告。这样后续阅读 v515/v519 时，不需要再猜 seed `515` 的 partial 是否只是格式化拆词导致。

本版不扩大模型、不新增训练数据、不改变 v513 alias matrix，也不把 normalized hit 包装成 strict success。它只增强已有 stability 报告的度量层，让 strict 与 normalized 结论并列出现。

## 前置链路

前置版本：

- v515：seed `514` full，seed `515` partial，因此只可声明 stable partial。
- v517：只读审计证明 v516 focus 产物存在 strict miss 但 normalized full。
- v518：把 strict/normalized 指标正式并入 focus 报告。

v519 回到 v515 这层稳定性实验，验证上游是否也存在同类 hidden normalized full。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_loss_alias_stability.py`
  - `summarize_loss_alias_seed_rows()` 现在会从每个 seed report 的 `generation_rows` 重新计算 normalized hit。
  - `summarize_loss_alias_stability()` 增加 normalized partial/full seed count、normalization gain count 和 metric decision。
  - `_decision()`、`_model_quality_claim()`、`_reason()`、`_next_action()` 增加 normalized signal 分支，但 strict full 仍然优先。
- `src/minigpt/model_capability_required_term_pair_loss_alias_stability_artifacts.py`
  - text/CSV/Markdown/HTML 全部输出 strict 与 normalized 稳定性指标。
- `tests/test_model_capability_required_term_pair_loss_alias_stability.py`
  - 增加 split-loss fake generation，保护 strict limited 但 normalized full 的边界。

## 核心数据结构

新增 seed 级字段：

- `generation_normalized_hit_case_count`
- `source_loss_normalized_hit`
- `heldout_loss_alias_normalized_hit_case_count`
- `heldout_loss_alias_normalized_full_coverage`
- `all_loss_alias_normalized_full_coverage`
- `normalization_gain_count`

新增 summary 字段：

- `loss_alias_stability_metric_decision`
- `source_loss_normalized_hit_seed_count`
- `heldout_loss_alias_normalized_partial_seed_count`
- `heldout_loss_alias_normalized_full_seed_count`
- `stable_loss_alias_normalized_full_coverage`
- `stable_loss_alias_normalized_partial_coverage`
- `all_seed_generation_normalized_hit_case_count`
- `normalization_gain_count`

`loss_alias_stability_decision` 仍然表示 strict 结论；`loss_alias_stability_metric_decision` 用来表达是否存在 strict 之外的 normalized 信号。

## 核心流程

1. stability builder 仍然逐 seed 调用 loss-alias objective。
2. 每个 seed report 保留原有 `generation_rows`。
3. `_normalized_seed_metrics()` 遍历 `generation_rows`，使用共享 `required_term_hit_metrics()` 判断 normalized hit 与 gain。
4. seed rows 写入 strict 与 normalized 两套字段。
5. summary 再按 seed rows 汇总稳定性。

这个流程没有改变训练行为，只把同一批输出解释得更完整。

## 真实结果解释

v519 真实运行结果：

```text
loss_alias_stability_decision=loss_alias_stable_partial_hit
loss_alias_stability_metric_decision=loss_alias_stable_partial_hit
heldout_loss_alias_full_seed_count=1
heldout_loss_alias_normalized_full_seed_count=1
stable_loss_alias_normalized_full_coverage=False
normalization_gain_count=0
```

seed `514` strict 与 normalized 都是 full；seed `515` strict 与 normalized 都是 partial。也就是说，v515 stability 源头没有隐藏 normalized full。v518 的 normalized full 是 focus 训练后出现的格式化拆词现象，而不是上游稳定性报告漏算。

## 测试覆盖

测试覆盖三类边界：

- strict full：normalized 也 full，但 gain 为 0。
- seed dependent：normalized 不改变 seed-dependent 事实。
- split loss：strict 不稳定，但 normalized full，会进入 normalized stable signal 分支。

这些断言保护了本版最重要的边界：normalized signal 可以改变 metric decision，但不会伪造 strict stability。

## 运行证据

运行证据归档在：

```text
e/519/解释/model-capability-required-term-pair-loss-alias-stability-metrics/
e/519/图片/
```

截图：

```text
e/519/图片/01-model-capability-required-term-pair-loss-alias-stability-metrics.png
```

## 一句话总结

v519 把 loss-alias stability 从 strict-only 统计升级为 strict/normalized 双指标统计，并确认原始稳定性证据仍停在 stable partial。

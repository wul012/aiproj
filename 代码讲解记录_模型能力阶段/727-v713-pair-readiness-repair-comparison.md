# v713 pair-readiness repair comparison

## 本版目标和边界

v713 的目标是对比 v707 与 v712 两个真实训练结果，判断 v710-v712 的 loss-retention repair 是否值得继续。

本版不训练模型，不改 corpus；它是一次路线收口比较。

## 前置链路

```text
v707 base split training -> default direct hit count = 1
v708 diagnostic -> loss prompt absorbed by fixed
v709 plan -> loss-retention repair
v710 patch -> add loss-retention rows
v711 materialization -> patched corpus
v712 patched training -> default direct hit count = 0
```

v713 读取 v707 和 v712 的 training run reports。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_readiness_repair_comparison.py`
  - comparison builder。
  - 对比 baseline/candidate 的 pair-full、direct hit count、checkpoint 和 claim。

- `src/minigpt/model_capability_required_term_pair_readiness_repair_comparison_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_readiness_repair_comparison.py`
  - CLI。
  - 输入 `--baseline` 与 `--candidate`。

- `tests/test_model_capability_required_term_pair_readiness_repair_comparison.py`
  - 覆盖 regression、checkpoint missing 阻断、输出格式。

## 判定逻辑

核心比较：

```text
default_hit_delta = candidate_default_hit_count - baseline_default_hit_count
```

如果 candidate 有 pair-full 或 direct hits 增加，才算改善；如果 direct hits 减少，判定为 regression。

## 真实结果

v713 输出：

```text
decision=pair_readiness_loss_retention_patch_regressed
default_hit_delta=-1
candidate_improved=False
candidate_regressed=True
```

这说明 loss-retention patch 不是有效方向。

## 工程意义

这版很重要，因为它阻止继续沿着“单边 prefix 加权”惯性推进。项目现在有足够证据说明：

- base split 能保住 fixed。
- loss-retention patch 没保住 loss，还损伤 fixed。
- 继续增加同类 rows 很可能继续制造前缀循环。

后续如果继续做模型能力，应转向更结构化的训练目标、模型容量对比、或 decode/eval 设计，而不是继续单边 prefix weighting。

## 一句话总结

v713 用真实训练对比关闭 loss-retention prefix repair 路线，给下一阶段模型能力探索留下清晰边界。

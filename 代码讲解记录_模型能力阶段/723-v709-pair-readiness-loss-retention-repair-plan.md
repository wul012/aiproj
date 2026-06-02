# v709 pair-readiness loss-retention repair plan

## 本版目标和边界

v709 的目标是把 v708 的 heldout failure diagnostic 转成 loss-retention repair plan。

本版不训练、不改 corpus、不生成 checkpoint，只生成下一步 contract patch 的计划。

## 前置链路

v708 输出：

```text
decision=pair_readiness_loss_prompt_absorbed_by_fixed
dominant_failure=loss_prompt_absorbed_by_fixed
loss_hit_count=0
loss_prompt_fixed_pollution_count=1
```

因此 v709 的计划必须聚焦 loss retention，而不是泛泛增加样本。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_readiness_loss_retention_repair_plan.py`
  - plan builder。
  - 检查 diagnostic 是否 pass、decision 是否对应 loss prompt fixed-pollution、loss 是否未命中、fixed pollution 是否存在。

- `src/minigpt/model_capability_required_term_pair_readiness_loss_retention_repair_plan_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_readiness_loss_retention_repair_plan.py`
  - CLI。
  - 输入 v708 diagnostic JSON 或目录。

- `tests/test_model_capability_required_term_pair_readiness_loss_retention_repair_plan.py`
  - 覆盖 ready、错误 failure mode 阻断、输出格式。

## Check 设计

v709 检查：

```text
diagnostic_passed
diagnostic_decision
loss_missing
fixed_dominance_observed
```

这些检查保证 repair plan 只在“loss prompt 被 fixed 吸附”这个明确条件下产生。

## Plan 内容

输出 plan：

```text
proposed_next_artifact=pair_readiness_loss_retention_contract_patch
repair_focus=restore loss direct retention without sacrificing fixed direct retention
```

contract patch：

```text
duplicate loss prefix progression rows
add loss anti-fixed contamination rows
keep fixed direct rows unchanged
keep heldout pair probe excluded from training
```

## 一句话总结

v709 把 v708 的 fixed-dominance 失败归因转成 loss-retention contract patch 计划，为下一版真正 patch 训练输入做准备。

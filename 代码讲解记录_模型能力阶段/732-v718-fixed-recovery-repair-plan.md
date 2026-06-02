# v718 fixed-recovery repair plan

## 本版目标和边界

v718 的目标是从 v717 route comparison 生成 fixed-recovery repair plan。

本版不修改 corpus，不训练模型，也不声称模型能力提升。它只是把 v716 的具体失败形态转成下一版 contract patch 的边界。

## 前置链路

```text
v716 structured-template training
 -> hit_terms=['loss']
 -> missed_terms=['fixed']
v717 route comparison
 -> structured-template ties baseline hit count
 -> failure_shape_changed=True
v718 fixed-recovery repair plan
 -> propose fixed-recovery contract patch
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_recovery_repair_plan.py`
  - repair plan builder。
  - 读取 v717 route comparison。
  - 校验 structured-template 是否确实 hit loss、miss fixed。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_recovery_repair_plan_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_readiness_fixed_recovery_repair_plan.py`
  - CLI。
  - 输入 v717 comparison JSON 或目录。

- `tests/test_model_capability_required_term_pair_readiness_fixed_recovery_repair_plan.py`
  - 覆盖 plan ready、pair-full source 阻断、structured 不 miss fixed 阻断、输出格式。

## 校验逻辑

v718 的关键 checks：

- `route_comparison_passed`
  - v717 comparison 必须 pass。

- `route_comparison_decision`
  - 必须是 `pair_readiness_structured_template_changes_failure_shape_without_pair_full`。

- `structured_hits_loss`
  - structured route 必须已经命中 `loss`。

- `structured_misses_fixed`
  - structured route 必须 miss `fixed`。

- `no_pair_full_route`
  - 不能已经有 pair-full route。

- `structured_not_above_baseline`
  - structured 不能被误认为已经超过 baseline。

这些检查让 v718 只在“loss 已恢复但 fixed 丢失”的具体场景下生成 fixed-recovery plan。

## Plan 内容

下一步 artifact：

```text
pair_readiness_fixed_recovery_contract_patch
```

patch 建议：

```text
add fixed answer confirmation rows after structured prompt-answer rows
add fixed anti-loss contamination rows
preserve loss structured rows from v714 because loss recovered in v716
keep heldout pair probe excluded from training rows
compare fixed-recovery run against v707 baseline and v716 structured-template before any promotion
```

这里的关键是“恢复 fixed，但保留 loss”。v712 的教训是单边强化会破坏另一边；v718 明确要求 patch 之后还要和 v707/v716 比较。

## 输出和证据

运行证据：

- `e/718/解释/model-capability-required-term-pair-readiness-fixed-recovery-repair-plan/`
- `e/718/图片/v718-fixed-recovery-repair-plan.png`

关键输出：

```text
status=pass
decision=pair_readiness_fixed_recovery_repair_plan_ready
plan_ready=True
source_structured_hit_terms=['loss']
source_structured_missed_terms=['fixed']
model_quality_claim=plan_only
```

## 一句话总结

v718 把 structured-template 的 loss-only 结果转成 fixed-recovery plan，为下一版 contract patch 定义了“不破坏 loss、恢复 fixed”的边界。

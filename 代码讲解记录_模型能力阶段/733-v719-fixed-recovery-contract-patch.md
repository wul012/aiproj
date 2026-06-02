# v719 fixed-recovery contract patch

## 本版目标和边界

v719 的目标是把 v718 plan 变成可 materialize 的 contract patch。

本版不训练模型，不生成 corpus，也不做 promotion。它只在 v714 structured-template contract 的基础上追加 fixed-recovery rows。

## 前置链路

```text
v716 structured-template training -> hit loss, miss fixed
v717 route comparison -> failure shape changed
v718 fixed-recovery repair plan -> propose contract patch
v719 fixed-recovery contract patch -> ready for materialization
```

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_recovery_contract_patch.py`
  - contract patch builder。
  - 读取 v718 plan 和 v714 base contract。
  - 追加 fixed-recovery rows，保留 structured loss rows。

- `src/minigpt/model_capability_required_term_pair_readiness_fixed_recovery_contract_patch_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/run_model_capability_required_term_pair_readiness_fixed_recovery_contract_patch.py`
  - CLI。
  - 输入 repair plan 与 base contract。

- `src/minigpt/model_capability_required_term_pair_readiness_corpus_materialization.py`
  - ready decision 白名单增加 `pair_readiness_fixed_recovery_contract_patch_ready`。
  - locator 文件名表增加 fixed-recovery contract patch JSON。

- `tests/test_model_capability_required_term_pair_readiness_fixed_recovery_contract_patch.py`
  - 覆盖 patch ready、可 materialize、错误 base contract 阻断、输出格式。

## 核心 patch rows

v719 追加 8 条 fixed-recovery rows：

```text
task: complete required term | prompt: fixed= | answer: fixed | recovery: fixed
case=fixed-recovery | prompt=fixed= | expected=fixed | answer=fixed
fixed direct answer confirmation -> fixed
fixed prompt should complete fixed before loss
fixed branch keeps fixed and rejects loss completion
fixed recovery row preserves fixed token sequence
when prompt begins fixed= the answer remains fixed
required term fixed stays fixed while loss rows stay present
```

这些 rows 的设计边界：

- 只补 fixed direct recovery。
- 不删除 v714 structured-template loss rows。
- 不加入 heldout pair probe `fixed=|loss=`。

## 校验逻辑

核心 checks：

- `repair_plan_decision`
  - 必须来自 v718 ready plan。

- `base_contract_decision`
  - base 必须是 v714 structured-template contract。

- `fixed_rows_added`
  - 所有 fixed-recovery rows 必须存在。

- `loss_rows_preserved`
  - loss structured rows 仍要保留。

- `no_exact_eval_row_overlap`
  - training rows 不与 `fixed=`、`loss=`、`fixed=|loss=` 精确重叠。

- `heldout_pair_absent`
  - heldout pair 不能成为 training row。

## 输出和证据

运行证据：

- `e/719/解释/model-capability-required-term-pair-readiness-fixed-recovery-contract-patch/`
- `e/719/图片/v719-fixed-recovery-contract-patch.png`

关键输出：

```text
status=pass
decision=pair_readiness_fixed_recovery_contract_patch_ready
base_training_row_count=14
patched_training_row_count=22
added_training_row_count=8
loss_row_count=11
model_quality_claim=contract_patch_only
```

## 一句话总结

v719 把 fixed-recovery 计划落成可 materialize 的 contract patch，明确下一步只能用真实训练验证 fixed 是否恢复且 loss 是否保留。

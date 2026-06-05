# v887 stabilized loss-suffix uptake stagnation diagnostic 代码讲解

## 本版目标和边界

v887 接在 v886 replay 之后，目标是比较 v882 与 v886 两次 replay 的逐 case 变化。v886 已经证明 v885 checkpoint 没有恢复 bounded objective contract，但还需要弄清楚“完全没变化”还是“有表面变化但没有能力增益”。

本版不训练、不写新 patch、不改 contract。它只读两个 replay report，输出 delta diagnostic，为下一步 repair plan 提供依据。

## 关键文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic.py`
  - 构建 v887 诊断报告。
  - 对齐 baseline/current replay rows，并计算 pass、any-hit、zero-hit、continuation、loss hit 的变化。
- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic_artifacts.py`
  - 写出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 summary card 和逐 case delta 表。
- `scripts/diagnose_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation.py`
  - CLI 入口，接收 baseline replay 和 current replay。
  - `--require-diagnostic-ready` 让失败诊断以退出码暴露。
- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_stagnation_diagnostic.py`
  - 覆盖完全停滞、格式变化但无增益、loss 新增命中、case 集合变化、CLI 输出。

## 核心数据结构

每条 case delta 包含：

```text
case_id
baseline_continuation
current_continuation
continuation_changed
baseline_hit_terms
current_hit_terms
hit_terms_changed
loss_newly_hit
current_fixed_l_partial
state_label
```

其中 `state_label` 用来区分：

- `unchanged_fixed_l_partial`：continuation 和 hit terms 都没变。
- `changed_fixed_l_partial`：仍是 fixed-l partial，但文本形态变化。
- `loss_recovered`：current 新增 `loss` 命中。
- `zero_hit_regression`：current 退回 zero-hit。
- `other_partial`：其他部分命中状态。

## 判定规则

v887 不再要求 continuation 完全相同才通过。真实 v886 数据显示，有 2 条 continuation 发生了格式变化，但没有新增 `loss`，也没有新增 pass。因此本版主判据是：

```text
no_contract_gain_confirmed =
  current_fixed_l_partial_case_count == case_count
  pass_delta == 0
  any_hit_delta == 0
  zero_hit_delta == 0
  loss_newly_hit_case_count == 0
  objective_contract_recovered == False
```

如果 continuation 也完全不变，则是 `stagnation_confirmed=True`。如果 continuation 变了但上述能力指标不变，则是 `surface_format_changed_without_suffix_gain=True`。

## 本版真实结论

真实 v882 -> v886 对比结果：

```text
no_contract_gain_confirmed=True
stagnation_confirmed=False
surface_format_changed_without_suffix_gain=True
pass_delta=0
any_hit_delta=0
zero_hit_delta=0
continuation_changed_count=2
loss_newly_hit_case_count=0
```

这说明 v885 训练改变了一些 surface formatting，但没有把 `loss` suffix 带进 replay contract。

## 测试覆盖

测试覆盖四个关键保护点：

- 完全 unchanged fixed-l partial 时，诊断通过并给出 stagnated decision。
- 只有 formatting delta、没有 suffix gain 时，诊断也通过，但 decision 明确是 `surface_format_changed_without_suffix_gain`。
- 如果 current 新增 `loss` 命中，stagnation 诊断失败，避免误伤真实进步。
- 如果 case 集合不一致，诊断失败，避免错位比较。

## 一句话总结

v887 把 v885 的训练结果从“可能没用”精确收敛为“有表面格式变化，但没有 contract-level suffix gain”。

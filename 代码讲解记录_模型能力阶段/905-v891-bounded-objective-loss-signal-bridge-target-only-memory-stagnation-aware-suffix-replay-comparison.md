# v891 stagnation-aware suffix replay comparison 代码讲解

## 本版目标和边界

v891 承接 v890 训练产物。v890 的训练 loss 下降，但 sample 没有完整输出 `fixed loss`；v891 的目标是用 unchanged v836 bounded objective contract 做真实 replay，判断这条 stagnation-aware suffix 路线是否恢复 contract。

本版不训练、不改数据、不做 holdout。它只复核 v890 checkpoint 的 contract 表现。

## 关键文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison.py`
  - v891 专属 replay wrapper。
  - 复用通用 replay core，只适配 v890 training ready 字段、route、decision 和 next step。
- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison.py`
  - CLI 入口，接收 contract、training run、checkpoint、tokenizer。
- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_replay_comparison.py`
  - 覆盖 partial hit、contract recovered holdout、training not ready、CLI 输出。

## 核心适配

v890 training report 的 ready 字段是：

```text
bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_training_ready
```

通用 replay core 需要：

```text
bounded_objective_loss_signal_bridge_training_ready
```

v891 的 `_adapt_training_run()` 只做这层字段映射，保持 replay core 不变。这样可以继续用同一套 contract 逻辑比较不同训练路线。

## 本版真实结果

真实 replay 结果：

```text
case_count=3
passed_case_count=0
any_hit_case_count=3
zero_hit_case_count=0
objective_contract_recovered=False
promotion_ready=False
```

三条 continuation：

```text
canonical_direct_completion -> "\nfixed l"
minimal_direct_completion -> "\nfixed l"
completion_label_surface -> "\nfixed l"
```

这说明 v889/v890 的修复把 surface formatting 统一到换行 `fixed l`，但仍没有让 `loss` suffix 出现。

## 测试覆盖

测试覆盖四个方向：

- partial hit 时报告 ready，但不允许 promotion。
- contract recovered 时进入 holdout-required，而不是直接通过。
- training ready 为 false 时 replay 失败并记录 issue。
- CLI 能从目录定位 JSON 并写出五类 artifact。

## 一句话总结

v891 证明 stagnation-aware suffix 训练仍没有恢复 contract，只把三条 replay surface 统一到了换行 fixed-l partial state。

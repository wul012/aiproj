# v888 stagnation-aware suffix repair plan 代码讲解

## 本版目标和边界

v888 承接 v887 的诊断结果。v887 已经证明 v885 checkpoint 没有带来 contract-level suffix gain：`pass_delta=0`、`any_hit_delta=0`、`zero_hit_delta=0`、`loss_newly_hit_case_count=0`，同时有 `surface_format_changed_without_suffix_gain=True`。

本版目标是把这些诊断结果转成下一版 patch 的可执行计划。它不写训练语料，不启动训练，不做 replay，也不声称模型能力提升。

## 关键文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan.py`
  - 读取 v887 stagnation diagnostic。
  - 校验 no-contract-gain、loss 未新增命中、case diagnostics 存在。
  - 生成五类 repair action。
- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan_artifacts.py`
  - 写出 JSON、CSV、TXT、Markdown、HTML。
  - HTML 展示 summary card 和 plan actions 表。
- `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan.py`
  - CLI 入口。
  - 支持 `--require-plan-ready`，让计划生成失败能通过退出码暴露。
- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_repair_plan.py`
  - 覆盖 ready plan、no-contract-gain 缺失、loss 已新增命中、CLI 输出。

## 核心输入条件

v888 必须看到下面这些条件才会输出 ready plan：

```text
source diagnostic status == pass
stagnation diagnostic ready == True
no_contract_gain_confirmed == True
loss_newly_hit_case_count == 0
case_diagnostics 非空
source next_step 指向本 plan
```

这样做是为了避免误伤真实进步。如果上一版已经新增 `loss` 命中，v888 会失败，而不是继续按“停滞”路线生成 patch。

## 五类 repair action

计划输出五个 action：

1. `suffix-position-bridge`
   - 让 `loss` 直接跟在 `fixed l` 和 `fixed lo` fragment 后。
2. `surface-format-normalization`
   - 同时保留空格前缀和换行前缀，避免 v887 观察到的 formatting drift 再次发生。
3. `replay-prompt-boundary-lock`
   - 把 patch 绑定到 unchanged v836 contract prompts。
4. `suffix-ratio-increase`
   - 提高 suffix uptake 样本与 surface carry-forward 样本的比例。
5. `contract-gated-training-stop`
   - 明确 sample 命中不能替代 replay 验收。

## 本版真实结果

真实 v888 结果：

```text
status=pass
action_count=5
required_action_count=5
source_no_contract_gain_confirmed=True
source_surface_format_changed_without_suffix_gain=True
model_quality_claim=repair_plan_only
```

下一步 artifact 是：

```text
bounded_objective_loss_signal_bridge_target_only_memory_stagnation_aware_suffix_patch
```

## 测试覆盖

测试保护四个点：

- 合法 v887 diagnostic 能生成 5 个 required action。
- `no_contract_gain_confirmed=False` 时失败，避免对真实进步误判。
- `loss_newly_hit_case_count>0` 时失败，避免覆盖已有 suffix gain。
- CLI 能从目录定位 diagnostic JSON，并写出五类 artifact。

## 一句话总结

v888 把“训练后无 contract gain”的负结果转化为下一版 patch 的约束清单，让后续优化从盲训转向有诊断依据的修复。

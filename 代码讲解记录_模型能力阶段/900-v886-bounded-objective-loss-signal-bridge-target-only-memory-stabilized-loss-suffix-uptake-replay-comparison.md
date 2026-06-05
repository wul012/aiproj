# v886 stabilized loss-suffix uptake replay comparison 代码讲解

## 本版目标和边界

v886 承接 v885 的真实训练产物，目标是对 unchanged v836 bounded objective contract 做 replay comparison。它验证的不是训练 loss，也不是 sample，而是三条固定 contract surface 是否都能生成完整 `fixed loss`。

本版不继续训练，不改 contract，不引入新 patch。它把 v885 checkpoint 放到同一套 objective contract 下复核，避免把 sample 命中误判成能力恢复。

## 关键文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison.py`
  - v886 专属 replay wrapper。
  - 复用通用 `build_bounded_objective_loss_signal_bridge_replay_comparison()`，只做 training ready 字段、route、decision、next step 的适配。
- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - 复用通用 replay renderer，并替换本版标题和 ready 字段。
- `scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison.py`
  - CLI 入口。
  - 接收 objective contract、training run、checkpoint、tokenizer 和 device。
- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_replay_comparison.py`
  - 覆盖 partial hit、contract recovered holdout、training not ready、CLI/artifact wiring。

## 核心适配逻辑

v885 training report 的 ready 字段是：

```text
bounded_objective_loss_signal_bridge_target_only_memory_stabilized_loss_suffix_uptake_training_ready
```

通用 replay core 读取的是：

```text
bounded_objective_loss_signal_bridge_training_ready
```

因此 v886 的 `_adapt_training_run()` 只做字段映射，不改训练报告本身。这样 replay core 仍保持统一，v886 只负责表达“这是 stabilized loss-suffix uptake 路线的 replay”。

## 运行流程

1. CLI 读取 v836 contract JSON。
2. CLI 读取 v885 training-run JSON。
3. 传入 v885 checkpoint 和 tokenizer。
4. 通用 replay core 逐条执行 contract case。
5. v886 wrapper 把结果改写成本路线的 decision、summary、interpretation。
6. artifacts writer 写出 JSON/CSV/TXT/Markdown/HTML。

## 本版结果

真实 replay 结果：

```text
case_count=3
passed_case_count=0
any_hit_case_count=3
zero_hit_case_count=0
objective_contract_recovered=False
promotion_ready=False
```

三条 case 的 continuation：

```text
canonical_direct_completion -> " fixed l"
minimal_direct_completion -> "\nfixed l"
completion_label_surface -> "\nfixed l"
```

这说明 v885 sample 的 `fixed loss` 没有进入 contract replay。模型在固定 contract 解码条件下仍停在 `fixed l` partial state，只命中 `fixed`，缺失 `loss`。

## 测试覆盖

测试的重点不是 mock 出真实模型，而是保护 replay wrapper 的契约：

- partial hit 时，报告 `status=pass`，但 `objective_contract_recovered=False`。
- contract recovered 时，decision 进入 holdout-required，而不是直接 promotion。
- training ready 被置为 false 时，报告失败并包含 `training_ready` issue。
- CLI 能从目录定位 contract/training JSON，并写出五类 artifact。

## 一句话总结

v886 证明 v885 的训练产物仍只达到 partial required-term signal，下一步应先诊断为什么 `loss` suffix 没有进入 unchanged contract replay。

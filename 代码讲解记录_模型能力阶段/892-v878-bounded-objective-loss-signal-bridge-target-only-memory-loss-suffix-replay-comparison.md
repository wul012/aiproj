# v878：bounded objective loss signal bridge target-only memory loss-suffix replay comparison

## 本版目标和边界

v878 的目标是验证 v877 checkpoint 的真实 contract 表现。v877 sample 已经输出完整 `fixed loss`，但项目不能把 sample 当作模型能力证明。v878 因此继续使用不变的 v836 bounded objective contract 做三条 case replay。

本版不训练，不改 contract，不做 holdout promotion。它只回答：v877 的 sample 改善是否恢复了 bounded objective。

## 前置链路

```text
v876 loss-suffix patch
 -> v877 loss-suffix training run
 -> v878 loss-suffix replay comparison
```

这版是一个必要的校验刹车：避免因为单个 sample 变好就过度乐观。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison.py`
  - v878 核心 replay 适配模块。
  - 复用通用 `build_bounded_objective_loss_signal_bridge_replay_comparison()`。
  - 将 v877 training ready 字段映射到通用 replay engine。
  - route 标记为 `bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix`。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison_artifacts.py`
  - 复用已有 replay renderer。
  - 只替换标题和 ready 字段。

- `scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison.py`
  - CLI 入口。
  - 支持 objective contract、training run、checkpoint、tokenizer、device 和 require flags。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison.py`
  - 覆盖 partial-hit、contract recovered holdout required、training not ready、writer 和 CLI。

## 核心验证流程

v878 输入：

```text
contract: e/836/.../model_capability_route_promotion_bounded_objective_contract.json
training: e/877/.../bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_training_run.json
checkpoint: e/877/.../run/checkpoint.pt
tokenizer: e/877/.../run/tokenizer.json
```

输出 summary：

```text
objective_contract_recovered=False
passed_case_count=0
any_hit_case_count=2
zero_hit_case_count=1
promotion_ready=False
```

## Replay rows 解释

三条 case 的真实输出是：

```text
canonical_direct_completion -> "\nfixed l"
minimal_direct_completion   -> "\nfixed l"
completion_label_surface    -> "\nan: fix"
```

canonical/minimal 没有进一步突破 v874 的 `fixed l`；completion surface 反而从 v874 的 partial-hit 退回 zero-hit。这说明 v876/v877 的 loss-suffix patch 对 sample 有用，但对 contract surface 的稳定性不足。

## 与 v874 的差异

```text
v874: any_hit_case_count=3, zero_hit_case_count=0
v878: any_hit_case_count=2, zero_hit_case_count=1
```

所以 v878 不能写成能力提升版，只能写成 replay 回归/不稳定版。这个判断很关键：它让后续路线从“继续补 loss suffix”转向“诊断 completion surface regression”。

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_replay_comparison.py -q -o cache_dir=runs/pytest-cache-v878-focus
```

结果：

```text
4 passed
```

测试保护：

- partial-hit replay 只能说明 comparison ready，不能说明 recovered。
- contract recovered 仍然必须 holdout required。
- training not ready 时 replay 必须 fail。
- writer 和 CLI 必须输出 JSON、CSV、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/878/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-replay-comparison/`
- 截图目录：`e/878/图片/`
- Playwright MCP 截图：`e/878/图片/v878-bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-replay-comparison-html.png`

## 一句话总结

v878 用 replay 证明 sample 级完整输出没有恢复 objective contract，并把下一步方向转到 completion surface regression 诊断。

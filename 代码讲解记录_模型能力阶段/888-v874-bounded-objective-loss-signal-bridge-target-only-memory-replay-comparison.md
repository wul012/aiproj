# v874：bounded objective loss signal bridge target-only memory replay comparison

## 本版目标和边界

v874 的目标是对 v873 训练出的 target-only memory checkpoint 做真实 bounded objective replay comparison。v873 的 sample 已经出现 `fixed los`，但 sample 不能替代 contract。v874 用 v836 的三条 contract cases 做同口径验证。

本版不训练，不改 contract，不把 partial-hit 写成 pass。它只判断 v873 checkpoint 在原始 bounded objective 上是否恢复。

## 前置链路

```text
v872 target-only memory patch
 -> v873 target-only memory training run
 -> v874 target-only memory replay comparison
```

v874 是第一个真正回答“target-only memory 路线是否让模型能力变好”的版本。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison.py`
  - v874 核心 replay 适配模块。
  - 复用 `build_bounded_objective_loss_signal_bridge_replay_comparison()`。
  - 将 v873 training ready 字段映射为通用 loss-signal bridge training ready。
  - 把 route 写成 `bounded_objective_loss_signal_bridge_target_only_memory`。
  - 根据 recovered、any-hit、zero-hit 决定下一步诊断路径。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison_artifacts.py`
  - 复用已有 replay renderer。
  - 替换标题和 ready 字段，避免重复大 renderer。

- `scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison.py`
  - CLI 入口。
  - 支持 `--objective-contract`、`--training-run`、`--checkpoint`、`--tokenizer`、`--device`、`--require-comparison-ready`、`--require-objective-pass`。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison.py`
  - 覆盖 partial hit、contract recovered holdout required、training not ready、writer 和 CLI。

## 核心数据结构

v874 的输入 training summary 来自 v873：

```text
bounded_objective_loss_signal_bridge_target_only_memory_training_ready=True
final_train_loss=0.9454461932182312
final_val_loss=0.8332666158676147
train_loss_delta=-2.710383
decoder_anchor_example_count=0
```

`_adapt_training_run()` 只做一件事：

```text
bounded_objective_loss_signal_bridge_training_ready =
  bounded_objective_loss_signal_bridge_target_only_memory_training_ready
```

这样 replay engine 可以继续使用既有 checkpoint、tokenizer、contract case 逻辑，v874 只负责语义命名和下一步路由。

## 真实 replay 命令

```text
python -B scripts/run_bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison.py
  --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract
  --training-run e/873/解释/bounded-objective-loss-signal-bridge-target-only-memory-training-run
  --checkpoint e/873/解释/bounded-objective-loss-signal-bridge-target-only-memory-training-run/run/checkpoint.pt
  --tokenizer e/873/解释/bounded-objective-loss-signal-bridge-target-only-memory-training-run/run/tokenizer.json
  --device cpu
  --out-dir e/874/解释/bounded-objective-loss-signal-bridge-target-only-memory-replay-comparison
  --require-comparison-ready
  --force
```

输出：

```text
decision=bounded_objective_loss_signal_bridge_target_only_memory_replay_partial_required_term_hit
objective_contract_recovered=False
passed_case_count=0
any_hit_case_count=3
zero_hit_case_count=0
model_quality_claim=partial_required_term_signal
```

## Replay rows 解释

三条 case 的输出都命中 `fixed`，但都漏掉 `loss`：

```text
canonical_direct_completion -> "\nfixed l"
minimal_direct_completion   -> "\nfixed l"
completion_label_surface    -> "fixed l"
```

这说明 v872/v873 的 target-only memory patch 方向是有效的：它把模型从 v870 的 label echo / zero-hit 推到 `fixed` 前缀。但它仍然停在 `loss` 的前一个字符附近，尚未形成完整 `fixed loss`。

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_replay_comparison.py -q -o cache_dir=runs/pytest-cache-v874-focus
```

结果：

```text
4 passed
```

测试保护的点：

- partial-hit 必须 pass structure，但不能 recovered。
- contract recovered 仍然必须走 holdout required，不直接 promotion。
- training not ready 时 replay 必须 fail。
- CLI 和 writer 能生成 JSON、CSV、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/874/解释/bounded-objective-loss-signal-bridge-target-only-memory-replay-comparison/`
- 截图目录：`e/874/图片/`
- Playwright MCP 截图：`e/874/图片/v874-bounded-objective-loss-signal-bridge-target-only-memory-replay-comparison-html.png`

## 一句话总结

v874 首次把 target-only memory 路线转化为真实 replay 改善：三条 case 全部从 zero-hit 变成 partial-hit，但完整 contract 仍未恢复。

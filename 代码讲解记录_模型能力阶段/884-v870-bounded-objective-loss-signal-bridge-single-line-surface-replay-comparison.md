# v870：bounded objective loss signal bridge single-line surface replay comparison

## 本版目标和边界

v870 的目标是回放 v869 checkpoint，判断 v868 single-line patch 和 v869 训练是否真的改善了 bounded objective contract。v869 的 `final_val_loss=0.8147876858711243` 看起来更好，但 tiny GPT 的 loss 下降经常只说明它更会拟合训练语料，不等于能在固定 prompt 下输出目标答案。

本版不训练，不改 contract，不改 replay prompt，也不引入 decoder anchor。它只做真实 checkpoint replay，并把结果转成可追踪证据。

边界：

- 不把 v869 低 loss 解释为能力恢复。
- 不把 sample 当作 contract 结果。
- 不因 zero-hit 失败而修改历史证据。
- 不进行 promotion。

## 前置链路

```text
v867 label echo diagnostic
 -> v868 single-line surface patch
 -> v869 single-line surface training run
 -> v870 single-line surface replay comparison
```

v870 是这个小循环的裁判：只有它能说明 v868-v869 的修补是否在 objective contract 上生效。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison.py`
  - 核心 replay adapter。
  - 复用 `build_bounded_objective_loss_signal_bridge_replay_comparison()`。
  - 将 v869 training summary 映射为底层 replay 所需的 training-ready 字段。
  - 将输出 decision、summary、comparison 和 interpretation 改回 single-line surface 分支语义。

- `src/minigpt/bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - 复用 loss-signal bridge replay renderer，并替换标题和 ready 字段。

- `scripts/run_bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison.py`
  - CLI 入口。
  - 支持 objective contract、training run、checkpoint、tokenizer、device、out-dir 和 require flags。

- `tests/test_bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison.py`
  - 覆盖 partial hit、contract recovered、training not ready、writer 和 CLI。

- `e/870/解释/bounded-objective-loss-signal-bridge-single-line-surface-replay-comparison/`
  - v870 真实 replay 证据。

- `e/870/图片/v870-bounded-objective-loss-signal-bridge-single-line-surface-replay-comparison-html.png`
  - Playwright MCP 截图证据。

## 适配逻辑

v870 的核心不是重新写 replay，而是做正确语义映射。

输入的 v869 training report 中有：

```text
bounded_objective_loss_signal_bridge_single_line_surface_training_ready=True
```

底层 replay 需要：

```text
bounded_objective_loss_signal_bridge_training_ready=True
```

所以 `_adapt_training_run()` 把前者映射给底层模块。回放完成后，`_adapt_replay_report()` 再把结果改成本分支字段：

```text
bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison_ready
route=bounded_objective_loss_signal_bridge_single_line_surface
training_source=bounded_objective_loss_signal_bridge_single_line_surface_training_run
```

decision 映射也保持分支可读：

```text
bounded_objective_loss_signal_bridge_replay_zero_hit
 -> bounded_objective_loss_signal_bridge_single_line_surface_replay_zero_hit
```

## 真实回放命令

```text
python -B scripts/run_bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison.py
  --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract
  --training-run e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run
  --checkpoint e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run/run/checkpoint.pt
  --tokenizer e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run/run/tokenizer.json
  --device cpu
  --out-dir e/870/解释/bounded-objective-loss-signal-bridge-single-line-surface-replay-comparison
  --require-comparison-ready
  --force
```

输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_single_line_surface_replay_zero_hit
objective_contract_recovered=False
canonical_case_pass=False
case_count=3
passed_case_count=0
any_hit_case_count=0
zero_hit_case_count=3
pass_rate=0.0
promotion_ready=False
model_quality_claim=not_improved
```

## Replay Rows

三条 case 都没有命中 required terms：

```text
canonical_direct_completion
prompt: Answer with exactly two tokens: fixed loss
answer:
continuation: answer:
hit_terms: []
missed_terms: fixed, loss

minimal_direct_completion
prompt: Answer with exactly two words: fixed loss
answer:
continuation: answer:
hit_terms: []
missed_terms: fixed, loss

completion_label_surface
prompt: Complete with exactly two tokens: fixed loss
completion:
continuation: answeti
hit_terms: []
missed_terms: fixed, loss
```

这说明 v868-v869 的 single-line surface repair 没有解决 label echo/fragment 问题。尤其是前两个 case 仍然输出 `answer:`，和 v867 诊断很接近。

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison.py -q -o cache_dir=runs/pytest-cache-v870-focus
```

结果：

```text
4 passed
```

测试覆盖：

- partial hit 时 replay ready 但 contract not recovered。
- 全部 case pass 时必须进入 holdout required，而不是 promotion。
- training run 不 ready 时必须失败。
- writer 和 CLI 输出 JSON、CSV、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/870/解释/bounded-objective-loss-signal-bridge-single-line-surface-replay-comparison/`
- 截图目录：`e/870/图片/`
- Playwright MCP 截图：`e/870/图片/v870-bounded-objective-loss-signal-bridge-single-line-surface-replay-comparison-html.png`

## 一句话总结

v870 用真实 replay 证明 single-line surface patch training 没有恢复 objective contract，下一步应该诊断 zero-hit 形态并重新设计更强的输出约束，而不是把 loss 下降误认为能力提升。

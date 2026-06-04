# v866：bounded objective loss signal bridge pair-binding replay comparison

## 本版目标和边界

v866 的目标是用 v865 checkpoint 重新回放 v836 bounded objective contract，验证 v864/v865 pair-binding route 是否真正改善了模型输出。

v865 只是训练产物，不能说明能力恢复。v866 才是能力验收：同样三个 contract cases，同样 no-anchor replay，同样 required terms `fixed` 和 `loss`。

边界：

- 不训练。
- 不改 contract。
- 不使用 decoder anchor。
- 不 promotion。
- 不把训练 loss 下降解释成模型能力提升。

## 前置链路

```text
v864 pair-binding patch
 -> v865 pair-binding training run
 -> v866 pair-binding replay comparison
```

v866 对比的关键背景是 v862：v862 有两个 partial hits，而 v866 变成三个 zero-hit。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_pair_binding_replay_comparison.py`
  - v866 adapter。
  - 复用 v862 loss-signal bridge replay builder。
  - 把 v865 training ready 字段映射成 replay builder 能识别的输入。
  - 把输出 decision、summary、interpretation 改写成 pair-binding route。

- `src/minigpt/bounded_objective_loss_signal_bridge_pair_binding_replay_comparison_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/run_bounded_objective_loss_signal_bridge_pair_binding_replay_comparison.py`
  - CLI 入口。
  - 支持 `--objective-contract`、`--training-run`、`--checkpoint`、`--tokenizer`、`--device`、`--out-dir`、`--require-comparison-ready`、`--require-objective-pass`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_pair_binding_replay_comparison.py`
  - 覆盖 partial、recovered holdout、training not ready、writer 和 CLI。

- `e/866/解释/bounded-objective-loss-signal-bridge-pair-binding-replay-comparison/`
  - v866 真实 replay 证据。

- `e/866/图片/v866-bounded-objective-loss-signal-bridge-pair-binding-replay-comparison-html.png`
  - Playwright MCP 截图。

## adapter 映射

v865 training report 的 ready 字段：

```text
bounded_objective_loss_signal_bridge_pair_binding_training_ready
```

v862 replay builder 期望：

```text
bounded_objective_loss_signal_bridge_training_ready
```

v866 的 `_adapt_training_run()` 做这个映射，然后复用同一套 bounded objective replay scoring。

输出再改写为：

```text
bounded_objective_loss_signal_bridge_pair_binding_replay_comparison_ready
route=bounded_objective_loss_signal_bridge_pair_binding
training_source=bounded_objective_loss_signal_bridge_pair_binding_training_run
```

## 真实命令

```text
python -B scripts/run_bounded_objective_loss_signal_bridge_pair_binding_replay_comparison.py
  --objective-contract e/836/解释/model-capability-route-promotion-bounded-objective-contract
  --training-run e/865/解释/bounded-objective-loss-signal-bridge-pair-binding-training-run
  --device cpu
  --out-dir e/866/解释/bounded-objective-loss-signal-bridge-pair-binding-replay-comparison
  --require-comparison-ready
  --force
```

## 真实结果

```text
status=pass
decision=bounded_objective_loss_signal_bridge_pair_binding_replay_zero_hit
case_count=3
passed_case_count=0
any_hit_case_count=0
zero_hit_case_count=3
pass_rate=0.0
model_quality_claim=not_improved
```

case 级别：

```text
canonical_direct_completion -> continuation="answer:", missed=fixed/loss
minimal_direct_completion   -> continuation="answer:", missed=fixed/loss
completion_label_surface    -> continuation="ans", missed=fixed/loss
```

## 为什么这是重要负结果

v862 的结果是：

```text
passed_case_count=0
any_hit_case_count=2
zero_hit_case_count=1
```

v866 的结果是：

```text
passed_case_count=0
any_hit_case_count=0
zero_hit_case_count=3
```

这说明 v864/v865 pair-binding patch 没有把局部信号变成稳定输出，甚至让模型在该 decode profile 下更偏向标签碎片 `answer:` / `ans`。

因此下一步不应该继续堆同类 pair-binding 样本，而应该诊断：

- 是否 prompt/corpus 格式让模型学到了标签。
- 是否 newline 分隔削弱了 `fixed loss` 的连续性。
- 是否 max_new_tokens/temperature profile 需要同步复查。
- 是否需要单行 completion 样本而不是多行 pair-binding 样本。

## 测试覆盖

focused pytest 覆盖：

- partial replay ready 但不 recovered。
- recovered replay 仍需 holdout。
- training run not ready 阻断。
- writer + CLI。

```text
4 passed
```

运行证据：

```text
e/866/解释/bounded-objective-loss-signal-bridge-pair-binding-replay-comparison/
e/866/图片/v866-bounded-objective-loss-signal-bridge-pair-binding-replay-comparison-html.png
```

Playwright MCP snapshot 确认：

```text
Status=pass
Decision=bounded_objective_loss_signal_bridge_pair_binding_replay_zero_hit
Passed=0
Any hits=0
Zero hits=3
Claim=not_improved
```

## 一句话总结

v866 证明 pair-binding patch 训练没有改善 bounded objective replay，下一步必须诊断 zero-hit 回退，而不是继续盲目加样本。

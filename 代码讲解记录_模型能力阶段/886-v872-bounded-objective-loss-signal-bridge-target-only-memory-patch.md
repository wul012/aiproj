# v872：bounded objective loss signal bridge target-only memory patch

## 本版目标和边界

v872 的目标是把 v871 的 persisted label echo 诊断转成新的训练语料 patch。v871 已经说明 v869 训练虽然 loss 下降，但 v870 replay 仍然输出 `answer:` 和 `answeti`。这意味着继续在同样的标签 surface 上训练，很可能继续强化标签回声。

本版不训练，不 replay，不声明模型能力提升。它只构造 JSONL examples 和 patched corpus，供 v873 训练使用。

边界：

- 不修改 v836 objective contract。
- 不引入 decoder anchor。
- 不删除历史 single-line evidence。
- 不把 patch corpus 说成 checkpoint 能力。

## 前置链路

```text
v870 single-line surface replay zero-hit
 -> v871 zero-hit diagnostic
 -> v872 target-only memory patch
```

v872 是针对 v871 root causes 的修补版本。它的核心判断是：既然标签回声持续存在，就减少标签密度，强化 `fixed loss` 本身的短目标记忆。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_patch.py`
  - 核心 patch 构建模块。
  - 读取 v871 diagnostic、v870 replay comparison 和 v869 prepared corpus。
  - 生成 target-only、prompt-target、label-target 三类样本。
  - 检查 diagnostic ready、zero-hit replay、loss improved without uptake 和 no-anchor。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_patch_artifacts.py`
  - 输出 JSON、CSV、JSONL、corpus、TXT、Markdown、HTML。

- `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_patch.py`
  - CLI 入口。
  - 支持 `--zero-hit-diagnostic`、`--replay-comparison`、`--source-corpus`、`--out-dir`、`--require-patch-ready`、`--force`。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_patch.py`
  - 覆盖成功构建、loss-without-uptake 缺失时阻断、writer 和 CLI。

- `e/872/解释/bounded-objective-loss-signal-bridge-target-only-memory-patch/`
  - v872 真实 patch 证据。

- `e/872/图片/v872-bounded-objective-loss-signal-bridge-target-only-memory-patch-html.png`
  - Playwright MCP 截图证据。

## 样本结构

v872 每个 replay case 生成四条样本：

```text
target_only_completion_memory x2
prompt_target_memory x1
label_target_memory x1
```

三条 case 共 12 条，再加 12 条全局 target memory，所以总数是：

```text
patch_example_count=24
```

关键样本示例：

```text
fixed loss
```

用于强化目标答案本身。

```text
Answer with exactly two tokens: fixed loss fixed loss
```

用于将任务指令和目标答案直接相邻，避免末尾标签继续占据输出预算。

```text
answer:
fixed loss
```

用于保留最低限度的 label -> target 桥接，因为 replay prompt 仍含 `answer:` / `completion:`。

## 契约检查

`_checks()` 保护几条边界：

- `diagnostic_passed`
- `diagnostic_ready`
- `label_or_fragment_confirmed`
- `loss_improved_without_uptake`
- `replay_passed`
- `replay_ready`
- `zero_hit_replay`
- `patch_examples_present`
- `decoder_anchor_free`

其中最重要的是：

```text
loss_improved_without_uptake
```

它确保这个 patch 只用于“训练 loss 下降但 replay 零命中”的特定场景，而不是泛化地堆 target-only 样本。

## 真实构建命令

```text
python -B scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_patch.py
  --zero-hit-diagnostic e/871/解释/bounded-objective-loss-signal-bridge-single-line-surface-zero-hit-diagnostic
  --replay-comparison e/870/解释/bounded-objective-loss-signal-bridge-single-line-surface-replay-comparison
  --source-corpus e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run/run/prepared_corpus.txt
  --out-dir e/872/解释/bounded-objective-loss-signal-bridge-target-only-memory-patch
  --require-patch-ready
  --force
```

输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_target_only_memory_patch_ready
patch_example_count=24
target_only_example_count=14
prompt_target_memory_count=3
label_target_memory_count=3
decoder_anchor_example_count=0
model_quality_claim=target_only_memory_patch_only
next_step=train_bounded_objective_loss_signal_bridge_target_only_memory_patch
```

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_patch.py -q -o cache_dir=runs/pytest-cache-v872-focus
```

结果：

```text
3 passed
```

测试覆盖：

- 正常输入生成 24 条 patch examples。
- 如果不满足 `loss_improved_without_required_term_uptake=True`，patch 会失败。
- writer 和 CLI 能输出 JSON、CSV、JSONL、corpus、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/872/解释/bounded-objective-loss-signal-bridge-target-only-memory-patch/`
- 截图目录：`e/872/图片/`
- Playwright MCP 截图：`e/872/图片/v872-bounded-objective-loss-signal-bridge-target-only-memory-patch-html.png`

## 一句话总结

v872 将标签回声失败转化为低标签噪声的 target-only memory corpus，让下一版可以测试“先强化目标答案本身”是否比继续强化标签 surface 更有效。

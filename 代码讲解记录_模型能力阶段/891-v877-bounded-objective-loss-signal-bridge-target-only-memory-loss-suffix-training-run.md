# v877：bounded objective loss signal bridge target-only memory loss-suffix training run

## 本版目标和边界

v877 的目标是把 v876 loss-suffix patch corpus 训练成真实 checkpoint。v876 解决的是数据输入，本版解决的是训练产物。

本版不做 replay，不修改 v836 contract，不把 sample 输出等同于 contract recovered。它只记录一个可供 v878 replay 的 checkpoint。

## 前置链路

```text
v875 loss suffix diagnostic
 -> v876 loss-suffix patch corpus
 -> v877 real CPU training run
 -> v878 loss-suffix replay comparison
```

v877 的重要性在于真实训练结果已经出现完整 `fixed loss` sample，这说明 loss-suffix patch 的方向值得进入 replay。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_training_run.py`
  - v877 核心训练证据适配模块。
  - 将 v876 patch summary 映射为通用 loss-signal bridge training evidence。
  - 输出 `bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_training_ready`。

- `src/minigpt/bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_training_run_artifacts.py`
  - 复用已有 training-run renderer。
  - 只替换 ready 字段和标题，避免复制大 renderer。

- `scripts/build_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_training_run.py`
  - CLI 入口。
  - 构建 evidence 时保留 `run/` 子目录，避免误删 checkpoint。

- `tests/test_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_training_run.py`
  - 覆盖 ready、patch not ready、writer 和 CLI。

## 真实训练命令

```text
python scripts/train.py
  --prepared-data e/876/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-patch/bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_patch_corpus.txt
  --out-dir e/877/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-training-run/run
  --tokenizer char
  --batch-size 8
  --block-size 64
  --max-iters 220
  --eval-interval 10
  --eval-iters 5
  --learning-rate 0.001
  --train-ratio 0.9
  --n-layer 2
  --n-head 2
  --n-embd 64
  --dropout 0.0
  --seed 1877
  --device cpu
  --sample-prompt "Answer with exactly two tokens: fixed loss answer:"
  --sample-tokens 12
  --sample-temperature 0.8
  --sample-top-k 20
```

训练输出：

```text
final_step=220
final_train_loss=0.6454294323921204
final_val_loss=0.8692289590835571
train_loss_delta=-2.972881
```

## 样本输出解释

v877 的 sample：

```text
Answer with exactly two tokens: fixed loss answer: fixed loss
```

这比 v873 的 `fixed los` 又前进了一步，说明补 `loss` 后缀确实把 sample 推到了完整目标。但是 MiniGPT 项目现在的纪律是：sample 只能作为训练信号，不能替代 bounded objective replay。v878 必须用同一套 v836 contract 验证三条 cases。

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_target_only_memory_loss_suffix_training_run.py -q -o cache_dir=runs/pytest-cache-v877-focus
```

结果：

```text
3 passed
```

测试保护：

- patch ready 时 training run evidence 必须 pass。
- patch not ready 时必须 fail。
- writer 和 CLI 必须输出 JSON、CSV、TXT、Markdown、HTML。
- 下一步必须路由到 loss-suffix replay comparison。

## 运行证据

- 解释目录：`e/877/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-training-run/`
- 真实 run 目录：`e/877/解释/bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-training-run/run/`
- 截图目录：`e/877/图片/`
- Playwright MCP 截图：`e/877/图片/v877-bounded-objective-loss-signal-bridge-target-only-memory-loss-suffix-training-run-html.png`

## 一句话总结

v877 训练出了能在 sample 中完整生成 `fixed loss` 的 checkpoint，但仍把最终能力判断留给下一版同契约 replay。

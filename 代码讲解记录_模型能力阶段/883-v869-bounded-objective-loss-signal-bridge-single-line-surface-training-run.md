# v869：bounded objective loss signal bridge single-line surface training run

## 本版目标和边界

v869 的目标是把 v868 生成的 no-anchor single-line surface patch corpus 训练成一个真实 checkpoint。v868 只是训练语料，v869 才产生可被 replay 的模型产物。

本版仍然不修改 v836 objective contract，也不宣称模型能力已经恢复。训练 loss 下降只能证明模型拟合了这批语料；是否能在固定 objective cases 上输出 `fixed loss`，必须由下一版 replay 判断。

边界：

- 不改变 contract。
- 不改变 replay cases。
- 不引入 decoder anchor。
- 不把 sample 或 loss 单独当作通过证据。

## 前置链路

```text
v867 label echo diagnostic
 -> v868 single-line surface patch
 -> v869 single-line surface training run
 -> v870 replay comparison
```

v869 是训练产物版，承接 v868 的 patch corpus，并为 v870 提供 checkpoint、tokenizer、metrics 和 manifest。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_single_line_surface_training_run.py`
  - 核心训练证据适配模块。
  - 把 v868 patch summary 映射成已有 loss-signal bridge training-run 所需的字段。
  - 输出 single-line surface 语义的 decision、summary 和 next step。

- `src/minigpt/bounded_objective_loss_signal_bridge_single_line_surface_training_run_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - 复用已有 loss-signal bridge training-run renderer，并替换标题和 ready 字段名称。

- `scripts/build_bounded_objective_loss_signal_bridge_single_line_surface_training_run.py`
  - CLI 入口。
  - 读取 v868 patch JSON 和真实训练 run 目录。
  - 支持 `--require-training-ready` 和 `--force`。

- `tests/test_bounded_objective_loss_signal_bridge_single_line_surface_training_run.py`
  - 覆盖训练 run ready、patch not ready 阻断、writer 和 CLI。

- `e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run/`
  - v869 真实训练证据目录，包含 run 子目录。

- `e/869/图片/v869-bounded-objective-loss-signal-bridge-single-line-surface-training-run-html.png`
  - Playwright MCP 截图证据。

## 适配逻辑

底层训练证据链已经存在于：

```text
build_bounded_objective_loss_signal_bridge_training_run()
```

v869 不复制训练检查逻辑，而是在 `_adapt_patch()` 中把 v868 summary 映射成底层模块能理解的字段：

```text
bounded_objective_loss_signal_bridge_single_line_surface_patch_ready
 -> bounded_objective_loss_signal_bridge_ready

patch_example_count
 -> bridge_example_count

single_line_case_example_count
 -> loss_signal_bridge_example_count

patched_corpus_char_count
 -> bridged_corpus_char_count
```

然后在 `_adapt_training_report()` 中把通用 training report 改回本阶段语义：

```text
bounded_objective_loss_signal_bridge_single_line_surface_training_ready
proposed_next_artifact=bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison
next_step=run_bounded_objective_loss_signal_bridge_single_line_surface_replay_comparison
```

这样做的好处是：训练 artifact 检查继续复用成熟路径，而业务语义仍然清楚地停留在 single-line surface branch。

## 真实训练命令

```text
python -B scripts/train.py
  --prepared-data e/868/解释/bounded-objective-loss-signal-bridge-single-line-surface-patch/bounded_objective_loss_signal_bridge_single_line_surface_patch_corpus.txt
  --out-dir e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run/run
  --tokenizer char
  --batch-size 8
  --block-size 64
  --max-iters 140
  --eval-interval 10
  --eval-iters 5
  --learning-rate 0.001
  --n-layer 2
  --n-head 2
  --n-embd 64
  --dropout 0.0
  --seed 1869
  --device cpu
  --sample-prompt "Answer with exactly two tokens: fixed loss answer:"
  --sample-tokens 12
  --sample-temperature 0.8
  --sample-top-k 20
```

训练结果：

```text
step=140 train_loss=1.2042 val_loss=0.8148
```

包装命令：

```text
python -B scripts/build_bounded_objective_loss_signal_bridge_single_line_surface_training_run.py
  --single-line-surface-patch e/868/解释/bounded-objective-loss-signal-bridge-single-line-surface-patch
  --run-dir e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run/run
  --out-dir e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run
  --require-training-ready
  --force
```

包装输出：

```text
status=pass
decision=bounded_objective_loss_signal_bridge_single_line_surface_training_run_ready
final_step=140
final_train_loss=1.2041561603546143
final_val_loss=0.8147876858711243
train_loss_delta=-2.376716
decoder_anchor_example_count=0
model_quality_claim=training_artifact_only
```

## Sample 边界

v869 的 sample 是：

```text
Answer with exactly two tokens: fixed loss answer: fansweved l
```

它没有恢复 `fixed loss`。这正是本版保持保守 claim 的原因：loss 下降是真实训练信号，但模型能力必须经过固定 contract replay。

## 测试覆盖

focused 测试：

```text
python -m pytest tests/test_bounded_objective_loss_signal_bridge_single_line_surface_training_run.py -q -o cache_dir=runs/pytest-cache-v869-focus
```

结果：

```text
3 passed
```

测试覆盖：

- patch ready + fake run 产物完整时，training report 为 pass。
- patch not ready 时，`--require-training-ready` 会返回失败。
- writer 和 CLI 能输出 JSON、CSV、TXT、Markdown、HTML。

## 运行证据

- 解释目录：`e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run/`
- run 目录：`e/869/解释/bounded-objective-loss-signal-bridge-single-line-surface-training-run/run/`
- 截图目录：`e/869/图片/`

## 一句话总结

v869 让 single-line surface repair 从“语料 patch”推进到“真实 checkpoint”，但能力是否改善仍被严格留给 v870 replay。

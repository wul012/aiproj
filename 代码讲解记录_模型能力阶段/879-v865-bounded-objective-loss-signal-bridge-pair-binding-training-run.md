# v865：bounded objective loss signal bridge pair-binding training run

## 本版目标和边界

v865 的目标是把 v864 pair-binding patch corpus 训练成一个真实 tiny checkpoint。

v864 只生成数据补丁，不能说明模型能力改善。v865 负责训练产物闭环：checkpoint、tokenizer、metrics、train config、run manifest、sample、loss curve 和 prepared corpus 都必须存在，并记录 loss 变化。

边界：

- 不 replay。
- 不 promotion。
- 不把 sample 当能力证据。
- 不使用 decoder anchor。

## 前置链路

```text
v863 partial-hit diagnostic
 -> v864 pair-binding patch
 -> v865 pair-binding training run
```

v865 的输出会交给 v866 replay comparison。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_pair_binding_training_run.py`
  - v865 adapter。
  - 复用 v861 的 loss-signal bridge training-run builder。
  - 把 v864 pair-binding patch summary 映射成通用 bridge training 输入。

- `src/minigpt/bounded_objective_loss_signal_bridge_pair_binding_training_run_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。

- `scripts/build_bounded_objective_loss_signal_bridge_pair_binding_training_run.py`
  - CLI 入口。
  - 保留 nested `run/` 目录，避免 `--force` 清掉训练产物。

- `tests/test_bounded_objective_loss_signal_bridge_pair_binding_training_run.py`
  - 覆盖 ready、patch not ready 阻断、writer 和 CLI。

- `e/865/解释/bounded-objective-loss-signal-bridge-pair-binding-training-run/`
  - v865 真实训练证据。

- `e/865/图片/v865-bounded-objective-loss-signal-bridge-pair-binding-training-run-html.png`
  - Playwright MCP 截图。

## adapter 映射

v864 patch 的 ready 字段是：

```text
bounded_objective_loss_signal_bridge_pair_binding_patch_ready
```

v861 training-run builder 期望看到：

```text
bounded_objective_loss_signal_bridge_ready
bridge_example_count
loss_signal_bridge_example_count
decoder_anchor_example_count
bridged_corpus_char_count
```

v865 的 `_adapt_patch()` 映射为：

```text
bounded_objective_loss_signal_bridge_ready
 <- bounded_objective_loss_signal_bridge_pair_binding_patch_ready

bridge_example_count
 <- patch_example_count

loss_signal_bridge_example_count
 <- pair_binding_example_count

bridged_corpus_char_count
 <- patched_corpus_char_count
```

训练完成后，v865 再把 summary 改写成：

```text
bounded_objective_loss_signal_bridge_pair_binding_training_ready=True
proposed_next_artifact=bounded_objective_loss_signal_bridge_pair_binding_replay_comparison
next_step=run_bounded_objective_loss_signal_bridge_pair_binding_replay_comparison
```

## 真实训练命令

```text
python -B scripts/train.py
  --prepared-data e/864/解释/bounded-objective-loss-signal-bridge-pair-binding-patch/bounded_objective_loss_signal_bridge_pair_binding_patch_corpus.txt
  --out-dir e/865/解释/bounded-objective-loss-signal-bridge-pair-binding-training-run/run
  --tokenizer char
  --batch-size 8
  --block-size 64
  --max-iters 120
  --eval-interval 10
  --eval-iters 5
  --learning-rate 0.001
  --n-layer 2
  --n-head 2
  --n-embd 64
  --dropout 0.0
  --seed 1865
  --device cpu
```

## 真实结果

```text
tokens=4771
vocab_size=44
parameters=107008
final_step=120
final_train_loss=1.2852036952972412
final_val_loss=1.0368845462799072
train_loss_delta=-2.32423
```

训练 run 产物：

```text
checkpoint.pt
tokenizer.json
metrics.jsonl
train_config.json
run_manifest.json
sample.txt
loss_curve.svg
prepared_corpus.txt
```

## sample 边界

sample 输出：

```text
Complete with exactly two tokens: fixed loss
completion:


ucaler:
p
```

它没有直接完成 `fixed loss`，所以 v865 不能 claim capability。真实能力必须由 v866 replay comparison 判定。

## 测试覆盖

focused pytest 覆盖：

- pair-binding patch ready + fake run artifacts -> training ready。
- patch not ready -> training run blocked。
- JSON/CSV/TXT/Markdown/HTML writer 和 CLI。

```text
3 passed
```

运行证据：

```text
e/865/解释/bounded-objective-loss-signal-bridge-pair-binding-training-run/
e/865/图片/v865-bounded-objective-loss-signal-bridge-pair-binding-training-run-html.png
```

Playwright MCP snapshot 确认：

```text
Status=pass
Decision=bounded_objective_loss_signal_bridge_pair_binding_training_run_ready
Final step=120
Val loss=1.0368845462799072
Decoder anchors=0
Claim=training_artifact_only
```

## 一句话总结

v865 完成 pair-binding patch 的真实训练闭环，但是否改善 bounded objective contract 仍必须等下一版 replay。

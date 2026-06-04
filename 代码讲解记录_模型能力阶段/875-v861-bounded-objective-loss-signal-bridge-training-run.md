# v861：bounded objective loss signal bridge training run

## 本版目标和边界

v861 的目标是把 v860 的 no-anchor bridge corpus 训练成一个真实 tiny checkpoint。

v860 只生成训练数据，不能证明模型能力。v861 负责训练产物闭环：checkpoint、tokenizer、metrics、train config、run manifest、sample、loss curve、prepared corpus 都必须存在，并记录 loss 变化。

边界：

- 不 replay。
- 不 promotion。
- 不根据 sample 直接判断 contract recovered。
- 不使用 decoder anchor。

## 前置链路

```text
v859 profile sweep
 -> v860 loss signal bridge corpus
 -> v861 loss signal bridge training run
```

v861 的输出会交给 v862 replay comparison。

## 关键新增文件

- `src/minigpt/bounded_objective_loss_signal_bridge_training_run.py`
  - v861 adapter。把 v860 bridge report 映射到底层 unassisted seed revision training-run evidence builder。
- `src/minigpt/bounded_objective_loss_signal_bridge_training_run_artifacts.py`
  - 输出 JSON/CSV/TXT/Markdown/HTML。
- `scripts/build_bounded_objective_loss_signal_bridge_training_run.py`
  - CLI 入口。
- `tests/test_bounded_objective_loss_signal_bridge_training_run.py`
  - 覆盖 ready、bridge not ready 阻断、writer 和 CLI。
- `e/861/解释/bounded-objective-loss-signal-bridge-training-run/`
  - 保存真实训练证据。
- `e/861/图片/v861-bounded-objective-loss-signal-bridge-training-run-html.png`
  - Playwright MCP 截图。

## adapter 映射

底层 builder 期望：

```text
bounded_objective_unassisted_repair_seed_revision_ready
example_count
direct_example_count
neutral_prompt_example_count
decoder_anchor_example_count
corpus_char_count
```

v861 adapter 从 v860 summary 映射：

```text
bounded_objective_loss_signal_bridge_ready
bridge_example_count
loss_signal_bridge_example_count
decoder_anchor_example_count
bridged_corpus_char_count
```

训练成功后再把输出改写为：

```text
bounded_objective_loss_signal_bridge_training_ready=True
proposed_next_artifact=bounded_objective_loss_signal_bridge_replay_comparison
next_step=run_bounded_objective_loss_signal_bridge_replay_comparison
```

## 真实训练命令

```text
python -B scripts/train.py
  --prepared-data e/860/解释/bounded-objective-loss-signal-bridge/bounded_objective_loss_signal_bridge_corpus.txt
  --out-dir e/861/解释/bounded-objective-loss-signal-bridge-training-run/run
  --tokenizer char
  --batch-size 8
  --block-size 64
  --max-iters 100
  --eval-interval 10
  --eval-iters 5
  --learning-rate 0.001
  --n-layer 2
  --n-head 2
  --n-embd 64
  --dropout 0.0
  --seed 1861
  --device cpu
```

## 真实结果

```text
final_step=100
final_train_loss=1.4715137481689453
final_val_loss=1.118106722831726
train_loss_delta=-2.121356
decoder_anchor_example_count=0
model_quality_claim=training_artifact_only
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

sample 是：

```text
Complete with exactly two tokens: fixed loss
completion: fixed los
c
```

它说明模型开始靠近 `fixed loss`，但还不是严格 contract pass。因此 v861 不 claim capability。

## 测试覆盖

focused pytest 覆盖：

- bridge ready + fake run artifacts -> training ready。
- bridge not ready -> training run blocked。
- JSON/CSV/TXT/Markdown/HTML writer 和 CLI。

```text
3 passed
```

运行证据：

```text
e/861/解释/bounded-objective-loss-signal-bridge-training-run/
e/861/图片/v861-bounded-objective-loss-signal-bridge-training-run-html.png
```

Playwright MCP snapshot 确认：

```text
Status=pass
Decision=bounded_objective_loss_signal_bridge_training_run_ready
Final step=100
Val loss=1.118106722831726
Decoder anchors=0
Claim=training_artifact_only
```

## 一句话总结

v861 完成了 loss-signal bridge 的真实训练闭环，把下一步推进到 checkpoint replay 验收。

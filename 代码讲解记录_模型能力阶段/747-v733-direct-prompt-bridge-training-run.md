# v733 direct-prompt bridge training run

## 本版目标和边界

v733 的目标是训练 v732 direct-prompt bridge corpus，并 replay heldout direct probes。

本版是真实训练版本，会生成 checkpoint、metrics、manifest、sample 和 replay report。它不做 promotion，因为 direct hits 仍为 0。

## 前置链路

```text
v730 surface mismatch diagnostic
 -> raw surface bridge needed
v731 direct-prompt bridge patch
 -> raw fixed=/loss= rows
v732 bridge corpus materialization
 -> 8320 training lines
v733 bridge training
 -> no direct hit
```

## 训练配置

v733 沿用 v729 配置：

```text
seed=3535
max_iters=1800
eval_iters=2
batch_size=16
block_size=16
n_layer=2
n_head=2
n_embd=96
learning_rate=0.01
max_new_tokens=12
temperature=0.2
top_k=1
device=cpu
```

这样 v729 与 v733 的差异主要来自 corpus patch，而不是模型规模或训练参数。

## 结果摘要

```text
status=pass
decision=pair_readiness_training_no_pair_full
training_status=pass
checkpoint_exists=True
pair_full_observed=False
default_continuation_hit_count=0
model_quality_claim=not_claimed
```

replay summary:

```text
default hit_terms=[]
default missed_terms=['fixed', 'loss']
suppress_newline_tokens hit_terms=[]
suppress_newline_tokens missed_terms=['fixed', 'loss']
```

continuation 细节：

```text
fixed= -> | | | ted |
loss=  -> fixed | | |
```

## 工程判断

v733 是 bridge patch 的真实负结果。

相比 v729，bridge patch 确实改变了 failure shape：v729 两个 prompt 都生成 non-term surface，而 v733 的 `loss=` 重新出现 fixed pollution。也就是说 raw surface bridge 没有解决 direct hit，反而把项目带回了早期 fixed-absorption 类问题。

## 证据

运行证据：

- `e/733/解释/model-capability-required-term-pair-readiness-direct-prompt-bridge-training-run/`
- `e/733/图片/v733-direct-prompt-bridge-training-run.png`

## 下一步

下一版应做 v729/v733 bridge comparison：

- 比较 hit count 是否改善。
- 比较 failure shape 是否从 non-term surface 变为 fixed pollution。
- 判断 bridge patch 是否应继续、回退或重设目标。

## 一句话总结

v733 证明 direct-prompt bridge patch 没有带来 direct hit，下一步应做对比诊断后再决定是否继续修补。

# v729 objective-structure training run

## 本版目标和边界

v729 的目标是训练 v728 objective-structure corpus，并 replay heldout direct probes。

本版是真实训练版本，会生成 checkpoint、metrics、manifest、sample 和 replay report。它不做 promotion，因为 pair-full 没出现，direct hit count 甚至降为 0。

## 前置链路

```text
v727 objective-structure contract
 -> task-id rows + paired block rows
v728 objective-structure corpus materialization
 -> 5760 training lines
v729 objective-structure training
 -> direct probes both miss
```

## 训练配置

v729 沿用 v724 capacity-probe 的配置，避免把变量混在一起：

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

这意味着 v729 主要测试的是 corpus/objective change，而不是新增模型容量。

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

continuation 细节显示：

```text
fixed= -> d | | | | |
loss=  -> d | | | | |
```

## 工程判断

v729 是一个有价值的负结果。

它说明当前 objective-structure rows 虽然更有结构，但没有让模型学会从 raw direct prompt `fixed=` / `loss=` 直接回到目标词。它与 v721/v724 的 fixed-only 不同：这里不是 fixed branch 吸收 loss，而是 direct prompt surface 和训练 row surface 之间出现 mismatch。

## 证据

运行证据：

- `e/729/解释/model-capability-required-term-pair-readiness-objective-structure-training-run/`
- `e/729/图片/v729-objective-structure-training-run.png`

训练目录保留 checkpoint、tokenizer、metrics、manifest、loss curve、sample 和 replay 报告。

## 下一步

下一版应做 surface mismatch diagnostic：

- 比较训练 rows 中的 prompt surface 与 heldout direct probes。
- 检查是否需要增加 direct prompt bridge rows。
- 仍然避免 exact heldout pair probe 泄漏。

## 一句话总结

v729 证明 objective-structure corpus 没有转化为 direct prompt 命中，后续应诊断 raw prompt surface mismatch，而不是继续盲目加容量。

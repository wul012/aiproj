# v724 capacity-probe training run

## 本版目标和边界

v724 的目标是执行 v723 capacity-probe plan。

本版真实训练模型，生成 checkpoint、metrics、manifest、sample 和 heldout replay。它不做 promotion，因为 pair-full 仍未出现。

## 前置链路

```text
v722 four-route comparison
 -> row patching closed
v723 capacity-probe plan
 -> larger tiny model config
v724 capacity-probe training
 -> real checkpoint + heldout replay
```

## 训练配置

v724 使用：

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

相比 v721：

- 层数：1 -> 2。
- heads：1 -> 2。
- embedding：64 -> 96。
- max_iters：1400 -> 1800。
- learning rate：0.02 -> 0.01。

## 结果摘要

输出：

```text
status=pass
decision=pair_readiness_training_no_pair_full
training_status=pass
checkpoint_exists=True
pair_full_observed=False
default_continuation_hit_count=1
model_quality_claim=not_claimed
```

replay:

```text
default: hit_terms=['fixed'], missed_terms=['loss'], pair_full=False
suppress_newline_tokens: hit_terms=['fixed'], missed_terms=['loss'], pair_full=False
```

case detail:

```text
fixed= -> fixed=fixed fixed
loss=  -> loss=fixed fixed
```

## 工程判断

v724 说明“稍微加容量”还不足以解决 direct pair readiness。

这个结果不等于容量路线完全无效，但它说明：

- 当前 fixed-recovery corpus 在更大 tiny 模型上仍会固定到 fixed branch。
- 继续小幅加 rows 或小幅加容量都需要先比较，不应直接进入更大训练。
- 下一步应做 v725 capacity comparison，把 v721/v724 与历史路线放在同一报告里。

## 证据

运行证据：

- `e/724/解释/model-capability-required-term-pair-readiness-capacity-probe-training-run/`
- `e/724/图片/v724-capacity-probe-training-run.png`

## 一句话总结

v724 用真实训练证明轻量 capacity probe 仍是 fixed-only，模型能力尚未突破 fixed/loss direct pair 共存。

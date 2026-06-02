# v721 fixed-recovery training run

## 本版目标和边界

v721 的目标是用 v720 fixed-recovery corpus 做真实 tiny training。

本版不新增代码，不做 promotion。它用真实 checkpoint 验证 fixed-recovery patch 是否能同时保留 `fixed` 和 `loss`。

## 前置链路

```text
v719 fixed-recovery contract patch
 -> v720 fixed-recovery corpus materialization
 -> v721 real tiny training + heldout direct replay
```

## 训练配置

v721 沿用 v707/v712/v716 的配置：

```text
seed=3535
max_iters=1400
batch_size=16
block_size=16
n_layer=1
n_head=1
n_embd=64
learning_rate=0.02
temperature=0.2
top_k=1
device=cpu
```

这样 v721 能和前三次训练公平比较。

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

replay variants：

```text
default: hit_terms=['fixed'], missed_terms=['loss'], pair_full=False
suppress_newline_tokens: hit_terms=['fixed'], missed_terms=['loss'], pair_full=False
```

case row 细节显示：

```text
fixed= -> fixed=fixed fixed
loss=  -> loss=fixed | | |
```

## 工程判断

v721 的价值是负面证据：

- v716 结构化模板能保住 loss，但 miss fixed。
- v721 fixed-recovery 能保住 fixed，但 loss 又被 fixed 吸走。
- 同一 tiny 配置下，简单行级权重/模板 patch 在两个分支间来回摇摆。

这说明下一步不应继续无限加单边 rows。更合理的路线是：

- 做 v722 route comparison，把 v707/v716/v721 放到同一张表。
- 如果仍无 pair-full，就把下一阶段转向 capacity 或训练目标结构，而不是继续局部 patch。

## 证据

运行证据：

- `e/721/解释/model-capability-required-term-pair-readiness-fixed-recovery-training-run/`
- `e/721/图片/v721-fixed-recovery-training-run.png`

## 一句话总结

v721 用真实训练证明 fixed-recovery patch 只把模型拉回 fixed-only，没有实现 fixed/loss 双分支共存。

# v645 required-term pair joint-cycle light-merge seed 3535

## 本版目标和边界

v645 训练 v644 的 light-merge corpus。目标是验证移除 heavy teacher-forced rows 后，是否能恢复 v630 的 generation pair-full。

本版是真实 tiny 训练，但仍只评价 fixed/loss required-term pair。

## 输入输出

输入：

```text
corpus_mode=equals_surface_no_pair_id_loss_internal_joint_cycle_light_merge_repair
seed=3535
repeat=320
bridge_repeat=24
max_iters=1800
```

输出：

```text
e/645/解释/model-capability-required-term-pair-joint-cycle-light-merge-seed-3535/
e/645/图片/v645-joint-cycle-light-merge-seed-3535.png
```

## 核心结果

```text
pair_full_observed=False
fixed= -> los=loss=los
loss=  -> loss=loss=lo
```

light-merge 恢复了 loss generation，但 fixed generation 被拉向 loss，因此仍是 tradeoff。

## 证据意义

v645 证明问题不是 teacher-forced rows 一个因素造成的；只要加入 internal loss 修复，生成层就容易向 loss 倾斜。

## 一句话总结

v645 把 light-merge 判为 loss-side tradeoff：比 v640 稳，但仍没有 aligned pair-full。

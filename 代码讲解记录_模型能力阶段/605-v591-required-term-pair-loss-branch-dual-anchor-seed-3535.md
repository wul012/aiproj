# v591 required-term pair loss-branch dual-anchor seed 3535

## 本版目标和边界

v591 是 v590 后的第二条真实 loss-branch objective 训练。它使用 `equals_surface_no_pair_id_loss_branch_dual_anchor_repair`，目标是检验“同一 clean record 绑定 fixed/loss”是否能缓解 v590 的 branch tradeoff。

本版不做新解码、不做多 seed 稳定性，也不改训练框架。它只比较 corpus 结构变化对 seed `3535` 的影响。

## 输入结构

dual-anchor corpus 的核心行是：

```text
loss=loss|fixed=fixed
fixed=fixed|loss=loss
anchor loss=loss
anchor fixed=fixed
```

这些行试图告诉模型：`loss` 和 `fixed` 是同一任务的两个正例分支，而不是互相排斥的负样本。

## 运行流程

v591 沿用 v590 的真实训练链路：

1. 生成 dual-anchor corpus。
2. 训练 tiny GPT checkpoint。
3. 用 `fixed=` 和 `loss=` 做 generation profile replay。
4. 汇总 hit/miss 和 pair-full。

## 关键结果

```text
training_status=pass
checkpoint_exists=True
pair_full_observed=False
hit_terms=loss
missed_terms=fixed
```

生成预览：

```text
fixed=lossssssssss
loss=lossssssssss
```

模型仍然偏向 `loss`，说明 dual-anchor 没能恢复 `fixed`。

## 证据链角色

`e/591` 是第二条真实训练证据。它和 v590 一起说明：当前 loss-heavy objective 能稳定拉出 `loss`，但也会把 `fixed` 压掉。

## 一句话总结

v591 证明 dual-anchor clean record 不足以消除 branch tradeoff，loss branch 被救回但 fixed 仍然掉线。

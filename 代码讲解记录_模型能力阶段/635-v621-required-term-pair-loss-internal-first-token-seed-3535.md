# v621 required-term pair loss-internal first-token seed 3535

## 本版目标和边界

v621 是 loss-internal-preference objective 的第二条真实训练。它选择更直接的 first-token 修复：让训练语料大量暴露 `loss=l`、`loss=lo`、`loss=los`、`loss=loss`。

本版不做路线选择；它只记录这一条 objective 的真实训练和 replay 结果。

## 输入和输出

输入模式：

```text
equals_surface_no_pair_id_loss_internal_first_token_repair
```

输出：

```text
e/621/解释/model-capability-required-term-pair-loss-internal-first-token-seed-3535/
e/621/图片/v621-loss-internal-first-token-seed-3535.png
```

## 运行流程

本版复用 `coexistence_refresh`：

1. 构造 first-token corpus。
2. 训练 seed `3535` tiny checkpoint。
3. 使用默认 profile 和 newline suppression profile replay `fixed=` / `loss=`。

## 关键结果

```text
training_status=pass
checkpoint_exists=True
pair_full_observed=False
```

replay 结果：

```text
fixed= -> l=lossssssss
loss=  -> loss=losssss
```

这说明 first-token 修复有真实作用：`loss=` 不再漂到 fixed；但它过度强化 loss，导致 `fixed=` 被破坏。

## 证据价值

v621 不是模型能力提升证据，而是 objective 设计证据：它告诉后续版本，`loss` 可以通过 first-token 路线恢复，但必须加 fixed-retention 约束。

## 一句话总结

v621 把 loss 分支救回来了一半，但代价是 fixed 分支丢失。

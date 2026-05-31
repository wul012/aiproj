# v602 required-term pair fixed-retention prompt-guard seed 3535

## 本版目标和边界

v602 是 fixed-retention objective 的第三条真实训练路线。它测试 prompt guard 是否能区分 `fixed=` 与 `loss=`，避免 v601 的 fixed-only 覆盖。

本版仍是训练证据，不做最终路线裁剪；裁剪交给下一版 comparison/decision。

## 输入

```text
corpus_mode=equals_surface_no_pair_id_fixed_retention_prompt_guard_repair
seed=3535
max_iters=1800
n_embd=64
device=cpu
```

## 关键结果

```text
training_status=pass
checkpoint_exists=True
pair_full_observed=False
```

生成行为：

```text
fixed= loss...
loss= losss...
```

## 链路意义

v602 没有继承 v601 的 fixed recovery，而是回到 loss-only。它说明 prompt guard 文本本身不足以克服 `fixed=` 的 retention gap。

## 一句话总结

v602 把 prompt-guard fixed-retention route 判定为 loss-only tradeoff。

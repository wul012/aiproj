# v601 required-term pair fixed-retention first-token seed 3535

## 本版目标和边界

v601 是 fixed-retention objective 的第二条真实训练路线，重点验证 first-token 修复是否能改变 `fixed=` 续写。

本版仍不宣称 pair-full；它记录的是一个有用 tradeoff：fixed 被恢复，loss 被覆盖。

## 输入

```text
corpus_mode=equals_surface_no_pair_id_fixed_retention_first_token_repair
seed=3535
max_iters=1800
n_embd=64
device=cpu
```

## 输出

```text
e/601/解释/model-capability-required-term-pair-fixed-retention-first-token-seed-3535/
```

## 关键结果

```text
pair_full_observed=False
fixed continuation_hit=True
loss continuation_hit=False
```

生成文本显示：

```text
fixed=fixed=fixed=
loss=fixed=fixed=
```

## 链路意义

v601 证明 v599 的 first-token repair 能改变模型行为，`fixed=` 不再直接漂到 loss；但它把 `loss=` 也拖向 fixed。这意味着后续目标不能只加 fixed 前缀链，需要更平衡的 prompt guard 或 route decision。

## 一句话总结

v601 把 fixed-retention first-token route 判定为 fixed-only tradeoff。

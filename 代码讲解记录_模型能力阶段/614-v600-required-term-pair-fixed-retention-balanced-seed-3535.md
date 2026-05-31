# v600 required-term pair fixed-retention balanced seed 3535

## 本版目标和边界

v600 是 v599 fixed-retention corpus 的第一条真实训练路线。它使用 balanced mode 检查 `fixed=` / `loss=` 是否能同时稳定。

本版不改变代码，不把一次训练失败视为退步；它的价值在于用真实 checkpoint 证明 balanced fixed-retention 不是足够的修复。

## 输入

```text
corpus_mode=equals_surface_no_pair_id_fixed_retention_balanced_repair
seed=3535
max_iters=1800
n_embd=64
device=cpu
```

## 输出

```text
e/600/解释/model-capability-required-term-pair-fixed-retention-balanced-seed-3535/
```

主要产物包括：

```text
checkpoint.pt
tokenizer.json
metrics.jsonl
model_capability_required_term_pair_coexistence_refresh.json
pair-generation-profile-replay/
```

## 关键结果

```text
training_status=pass
checkpoint_exists=True
pair_full_observed=False
```

生成面上仍然有 branch drift：

```text
fixed= losssssssss
loss=fixed= losss
```

## 链路意义

v600 说明 balanced fixed-retention 行还不够。虽然语料增加了 `fixed=fixed`，模型在 `fixed=` 后仍会偏向 `loss`，这与 v596 的 first-token gap 判断保持一致。

## 一句话总结

v600 把 fixed-retention balanced route 判定为真实训练下的 no pair-full 结果。

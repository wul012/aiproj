# v596 required-term pair loss-branch targeted missed-seed diagnostic

## 本版目标和边界

v596 读取 v595 的 3-seed targeted stability 报告，对每个 missed seed 做 first-token/logit 诊断。目标是判断 pair-full 失败是训练失败、解码问题，还是 first-token preference 问题。

本版不训练新 checkpoint，不新增 corpus，不推广 route。它是诊断层。

## 输入

```text
e/595/解释/model-capability-required-term-pair-loss-branch-targeted-seed-stability/
```

脚本会自动定位：

```text
model_capability_required_term_pair_colon_immediate_stability.json
```

## 输出

```text
model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.json
model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.csv
model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.md
model_capability_required_term_pair_colon_immediate_missed_seed_diagnostic.html
```

## 核心字段

每个 seed 的诊断行包含：

```text
first_token_decision
expected_top_count
fixed_expected_rank
loss_expected_rank
fixed_top_token
loss_top_token
observed_continuation_hit_count
```

这些字段直接说明 prompt 后第一 token 的偏好，不依赖文本解读猜测。

## 关键结果

```text
missed_seed_count=3
missed_first_token_gap_count=3
missed_expected_top_count=0
```

具体 rank：

```text
3535 fixed_rank=3 loss_rank=2
4535 fixed_rank=3 loss_rank=1
5535 fixed_rank=2 loss_rank=1
```

这说明 `loss` 路径已经足够强，而 `fixed` 的 first-token retention 不足。

## 证据链角色

`e/596` 是从 v595 稳定性失败到 v597 fixed-retention objective readiness 的桥。它避免继续误把问题理解为“loss 不够强”。

## 一句话总结

v596 证明 targeted loss branch 的失败核心是 fixed first-token retention gap，而不是 loss branch 训练不足。

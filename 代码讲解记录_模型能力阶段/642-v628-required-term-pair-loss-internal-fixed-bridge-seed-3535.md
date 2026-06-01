# v628 required-term pair loss-internal fixed-bridge seed 3535

## 本版目标和边界

v628 训练 v627 新增的 fixed-bridge corpus mode。它的目标是补 v626 发现的 fixed generation gap：v621 内部 fixed/loss 都匹配，但生成只命中 loss。

本版不做 promotion；它验证 bridge objective 是否能把内部偏好转成生成 pair-full。

## 输入和输出

输入模式：

```text
equals_surface_no_pair_id_loss_internal_fixed_bridge_repair
```

输出：

```text
e/628/解释/model-capability-required-term-pair-loss-internal-fixed-bridge-seed-3535/
e/628/解释/model-capability-required-term-pair-loss-internal-fixed-bridge-forced-choice/
e/628/图片/v628-loss-internal-fixed-bridge-seed-3535.png
e/628/图片/v628-loss-internal-fixed-bridge-forced-choice.png
```

## 训练结果

```text
training_status=pass
checkpoint_exists=True
pair_full_observed=False
```

replay：

```text
fixed= -> fixed= fixe
loss=  -> fixed= fixe
```

bridge objective 修复了 fixed generation，但同时破坏了 loss generation。

## Forced-choice 结果

```text
decision=refresh_forced_choice_partial_internal_match
expected_best_prompt_count=1
forced_choice_full_match_source_count=0
```

这比 v624 的 v621 internal full match 更弱，说明 fixed bridge 不只是生成层修补，它改变了内部偏好结构。

## 证据解释

v628 是重要的负结果：它证明单边补 fixed 会把系统推回 fixed-only，而不是把 v621 的 internal pair match释放到生成。

下一批 objective 应该设计联合约束，同时保留：

- `fixed=` 生成 fixed。
- `loss=` 生成 loss。
- forced-choice 内部 fixed/loss 都 expected-best。

## 一句话总结

v628 证明 fixed-only bridge 不是解法，下一步需要联合 internal/generation 约束。

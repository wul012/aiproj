# v662 required-term pair v630 light-merge resume

## 本版目标和边界

v662 是第二条真实 checkpoint continuation。它仍从 v630 generation pair-full checkpoint 出发，但换成 light-merge corpus，并降低学习率到 `0.001`，目标是减少 v660 那种强 internal-repair 对生成的破坏。

## 结果

- `training_mode=checkpoint_continuation`
- `resume_checkpoint_exists=True`
- `pair_full_observed=False`
- `fixed=` 未命中。
- `loss=` 命中。

## 解释

这说明破坏并不只来自 v660 的强 internal-repair 语料；即使是更轻的 merge continuation，也会把 v630 的 pair-full 推向 loss-only。

## 一句话总结

v662 证明更温和续训仍不能保住 generation pair-full，当前 checkpoint continuation 分支需要进入对比收口。

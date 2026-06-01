# v636 required-term pair alignment comparison with balanced-anchor

## 本版目标和边界

v636 重跑 v632 的 alignment comparison，但加入 v634/v635 balanced-anchor 证据。目标是验证第二个 joint variant 是否改变路线判断。

本版不新增代码能力，只复用 v632 comparison CLI 生成新证据。

## 输入输出

输入四条路线：

```text
loss-internal-first-token
loss-internal-fixed-bridge
loss-internal-joint-cycle
loss-internal-balanced-anchor
```

输出：

```text
e/636/解释/model-capability-required-term-pair-generation-internal-alignment-comparison-with-balanced-anchor/
e/636/图片/v636-generation-internal-alignment-comparison-with-balanced-anchor.png
```

## 核心结果

```text
decision=keep_generation_pair_full_and_repair_internal_preference
generation_pair_full_count=1
internal_pair_full_count=1
aligned_pair_full_count=0
```

路线分类：

```text
loss-internal-first-token     -> internal_pair_full_generation_gap
loss-internal-fixed-bridge    -> fixed_only_aligned_partial
loss-internal-joint-cycle     -> generation_pair_full_internal_partial
loss-internal-balanced-anchor -> fixed_only_aligned_partial
```

balanced-anchor 没有成为候选主线。

## 证据意义

v636 把 v634/v635 的负结果纳入统一矩阵，避免后续再次回到 balanced-anchor 方向。当前最合理路径仍是：

```text
base: loss-internal-joint-cycle
anchor: loss-internal-first-token
goal: preserve generation pair-full and repair loss internal preference
```

## 一句话总结

v636 证明 balanced-anchor 不改变主线判断，下一步应做 joint-cycle 的 internal repair。

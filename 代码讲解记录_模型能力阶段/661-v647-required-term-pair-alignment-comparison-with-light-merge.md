# v647 required-term pair alignment comparison with light-merge

## 本版目标和边界

v647 把 v645/v646 light-merge 证据纳入完整 generation/internal alignment comparison。

本版不新增模型训练，只做路线比较。

## 输入路线

```text
loss-internal-first-token
loss-internal-fixed-bridge
loss-internal-joint-cycle
loss-internal-balanced-anchor
joint-cycle-internal-repair
joint-cycle-light-merge
```

## 核心结果

```text
generation_pair_full_count=1
internal_pair_full_count=2
aligned_pair_full_count=0
```

light-merge 分类：

```text
partial_tradeoff
```

它不是 generation pair-full，也不是 internal pair-full。

## 证据意义

v647 把本轮两个新 corpus 分支都放入矩阵：

- heavy internal-repair：internal full，generation none。
- light-merge：generation loss-only，internal fixed-only。

二者都没有成为 aligned route。

## 一句话总结

v647 证明本轮 corpus 微调仍无法对齐 generation/internal，下一版应 closeout 而不是继续堆相似语料。

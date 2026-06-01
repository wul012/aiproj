# v637 required-term pair route decision with balanced-anchor

## 本版目标和边界

v637 消费 v636 的四路线 alignment comparison，重新生成 route decision。目标是确认 balanced-anchor 负结果纳入后，路线约束没有偏移。

本版不新增代码模块，只运行 v633 已有 route decision CLI。

## 输入和输出

输入：

```text
e/636/解释/model-capability-required-term-pair-generation-internal-alignment-comparison-with-balanced-anchor/
```

输出：

```text
e/637/解释/model-capability-required-term-pair-generation-internal-alignment-route-decision-with-balanced-anchor/
e/637/图片/v637-generation-internal-alignment-route-decision-with-balanced-anchor.png
```

## 核心结果

```text
decision=repair_internal_preference_preserve_generation_pair_full
selected_generation_route=loss-internal-joint-cycle
internal_anchor_route=loss-internal-first-token
direct_promotion_ready=False
```

这与 v633 一致，说明 balanced-anchor 加入后没有形成更好的候选。

## 证据意义

v637 是本轮训练分支的收束点：它让后续 v638 closeout 可以明确写出“保留 v630、排除 balanced-anchor、继续修 internal”。

## 一句话总结

v637 证明四路线加入后主线仍稳定，下一步应关闭本批次并设计 internal repair。

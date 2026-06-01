# v634 required-term pair loss-internal balanced-anchor seed 3535

## 本版目标和边界

v634 运行 v629 中预留的 `equals_surface_no_pair_id_loss_internal_balanced_anchor_repair`。它的目标是检验等权 anchor 是否能比 v630 joint-cycle 更稳地保持 fixed/loss 双生成。

本版不做 promotion；它是第二个 joint variant 的真实训练验证。

## 输入和输出

输入：

```text
corpus_mode=equals_surface_no_pair_id_loss_internal_balanced_anchor_repair
seed=3535
repeat=320
bridge_repeat=24
max_iters=1800
```

输出：

```text
e/634/解释/model-capability-required-term-pair-loss-internal-balanced-anchor-seed-3535/
e/634/图片/v634-loss-internal-balanced-anchor-seed-3535.png
```

## 核心结果

```text
decision=required_term_pair_coexistence_refresh_no_pair_full
training_status=pass
checkpoint_exists=True
pair_full_observed=False
```

replay：

```text
fixed= -> fixed fixed
loss=  -> fixed fixed
```

balanced-anchor 没有保住 loss generation，结果更接近 fixed-only。

## 链路角色

v634 帮助排除一个候选方向。它证明“等权重复 anchor”不等于真正的 fixed/loss 对齐；下一步仍应保留 v630 joint-cycle 的 generation pair-full 作为主线。

## 一句话总结

v634 证明 balanced-anchor 不是当前最优路线，v630 仍是 generation-preserving internal repair 的主要 base。

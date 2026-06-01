# v640 required-term pair joint-cycle internal-repair seed 3535

## 本版目标和边界

v640 训练 v639 新增的 joint-cycle internal-repair corpus。目标是验证这组语料是否能同时做到：

- 保住 v630 的 generation pair-full。
- 修复 v631 的 loss-side internal gap。

本版只评估 targeted fixed/loss required-term pair，不代表通用语言能力。

## 输入输出

输入：

```text
corpus_mode=equals_surface_no_pair_id_loss_internal_joint_cycle_internal_repair
seed=3535
repeat=320
bridge_repeat=24
max_iters=1800
```

输出：

```text
e/640/解释/model-capability-required-term-pair-joint-cycle-internal-repair-seed-3535/
e/640/图片/v640-joint-cycle-internal-repair-seed-3535.png
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
fixed= -> l losssssss
loss=  -> l sssssssss
```

这说明 v639 的语料没有保持 generation pair-full，甚至没有完整命中 `loss`。

## 证据意义

v640 证明“直接加强 internal repair rows”会干扰 generation surface。后续不能把 v639 corpus 当成成功路线，必须先通过 v641 forced-choice 判断 internal 是否有局部收益。

## 一句话总结

v640 把 v639 internal-repair corpus 判为生成层负结果：修 internal 的尝试破坏了 v630 的生成优势。

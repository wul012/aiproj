# v630 required-term pair loss-internal joint-cycle seed 3535

## 本版目标和边界

v630 对 v629 的 `equals_surface_no_pair_id_loss_internal_joint_cycle_repair` 做真实 tiny 训练。目标是验证 joint-cycle corpus 是否能避免 v628 的 fixed-only tradeoff。

本版只证明 fixed/loss 这组 required-term pair 的 targeted refresh signal，不说明模型具备通用语言能力提升。

## 输入和输出

输入：

```text
corpus_mode=equals_surface_no_pair_id_loss_internal_joint_cycle_repair
seed=3535
repeat=320
bridge_repeat=24
max_iters=1800
```

输出：

```text
e/630/解释/model-capability-required-term-pair-loss-internal-joint-cycle-seed-3535/
e/630/图片/v630-loss-internal-joint-cycle-seed-3535.png
```

## 核心结果

```text
status=pass
decision=required_term_pair_coexistence_refresh_pair_full_observed
training_status=pass
checkpoint_exists=True
pair_full_observed=True
default_pair_full_variant_count=1
suppression_pair_full_variant_count=1
```

replay case rows：

```text
default fixed= -> hit fixed
default loss=  -> hit loss
suppress_newline_tokens fixed= -> hit fixed
suppress_newline_tokens loss=  -> hit loss
```

这是与 v628 的核心差别：v628 只恢复 fixed，v630 同时保留 fixed/loss。

## 证据角色

`model_capability_required_term_pair_coexistence_refresh.json` 是后续比较模块的机器可读输入。

`required_term_pair_coexistence_refresh_corpus.txt` 是本轮训练语料快照，用于复核 v629 的 joint-cycle row 是否真实进入训练。

HTML 和截图是人工检查入口，用于确认 pair-full 状态没有被 README 或讲解误写。

## 后续风险

v630 只跑了一个 seed。它是重要正结果，但还不足以 promotion；下一步应运行 forced-choice 诊断和更多 seed 稳定性检查。

## 一句话总结

v630 第一次把 loss-internal 路线推到真实 pair-full checkpoint，但它仍是 targeted signal，需要继续验证稳定性。

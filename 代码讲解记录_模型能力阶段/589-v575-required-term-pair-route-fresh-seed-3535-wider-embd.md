# v575 required-term pair route fresh seed 3535 wider embedding

## 本版目标和边界

v575 做容量单变量检查。前面 v571、v573 都没有让 seed `3535` pair-full，v575 只把 `n_embd` 从 64 提到 96，验证问题是否来自 tiny 模型表达能力不足。

这一版不改语料、不改 decode、不改训练步数。它不是新路线，只是排除一个常见解释。

## 对比配置

v571：

```text
corpus_mode=equals_surface_no_pair_id_loss_balanced_repair
seed=3535
n_embd=64
```

v575：

```text
corpus_mode=equals_surface_no_pair_id_loss_balanced_repair
seed=3535
n_embd=96
```

其他核心参数保持一致。

## 真实结果

```text
pair_full_seed_count=0/1
continuation_hit_count=0
```

v571 还有一个 partial continuation hit，v575 连 partial hit 都没有保住。

## 证据文件

主报告：

```text
e/575/解释/model-capability-required-term-pair-route-fresh-seed-3535-wider-embd/model_capability_required_term_pair_colon_immediate_stability.json
```

训练产物：

```text
e/575/解释/model-capability-required-term-pair-route-fresh-seed-3535-wider-embd/seed-runs/seed-3535/
```

截图：

```text
e/575/图片/v575-route-fresh-seed-3535-wider-embd.png
```

## 链路角色

v575 的价值在于收窄问题空间。现在可以更有把握地说：fresh seed `3535` 的失败不是简单“模型太窄”，而是 objective 或 branch preference 设计没有稳定地绑定 `loss=` 到 loss branch。

## 一句话总结

v575 证明增大 embedding width 没有修复 seed 3535，后续应停止简单容量尝试，回到 objective/branch preference 设计。

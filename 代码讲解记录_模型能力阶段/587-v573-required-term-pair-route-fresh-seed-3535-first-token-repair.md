# v573 required-term pair route fresh seed 3535 first-token repair

## 本版目标和边界

v573 是 v572 诊断后的第一步验证。v572 发现 fresh seed `3535` 的失败卡在 `loss=` first-token preference，于是 v573 复用已有的 `equals_surface_no_pair_id_loss_balanced_first_token_repair`，看 full first-token rows 能不能修复这个 seed。

这一版不新增 corpus mode。这样做是有意克制：先验证旧修复是否有效，再决定是否需要新 objective。

## 输入路线

对比对象：

```text
v571: equals_surface_no_pair_id_loss_balanced_repair
v573: equals_surface_no_pair_id_loss_balanced_first_token_repair
```

二者训练预算、seed、decode 参数保持一致：

```text
seed=3535
max_iters=1400
n_embd=64
temperature=0.8
top_k=2
```

## 真实结果

v573 输出：

```text
pair_full_seed_count=0/1
continuation_hit_count=0
```

这比 v571 的 `continuation_hit_count=1` 更差。说明 full first-token rows 并没有让 fresh seed `3535` 学会 loss branch，反而削弱了原本的 partial hit。

## 证据文件

主报告：

```text
e/573/解释/model-capability-required-term-pair-route-fresh-seed-3535-first-token-repair/model_capability_required_term_pair_colon_immediate_stability.json
```

训练产物：

```text
e/573/解释/model-capability-required-term-pair-route-fresh-seed-3535-first-token-repair/seed-runs/seed-3535/
```

截图：

```text
e/573/图片/v573-route-fresh-seed-3535-first-token-repair.png
```

## 测试和验证

本版复用 colon-immediate stability runner。它覆盖：

- 训练命令执行。
- checkpoint/tokenizer 产物存在。
- generation profile replay。
- pair-full summary。

v573 的判断来自真实训练产物，而不是只读解释。

## 链路角色

v573 的作用是及时阻止一条看似合理但已经失败的修复路线。v572 说要修 first-token preference，但 v573 证明“已有 full first-token rows”不是答案。

## 一句话总结

v573 说明 fresh seed 3535 的 first-token gap 不能靠已有 full first-token repair rows 修复，下一步要做更精细的对比或新 objective 设计。

# v584 required-term pair target-anchor seed 3535

## 本版目标和边界

v584 接在 v583 route decision 后面。v583 停止 branch-binding v1/v2，并要求后续必须是更强 objective。v584 因此不继续改 binding 句，而是新增 target-anchor corpus，直接增加 exact equals continuation。

本版不做多 seed sweep，不扩大模型，不声称模型能力提升。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_target_anchor_corpus.py
src/minigpt/model_capability_required_term_pair_coexistence_corpus.py
tests/test_model_capability_required_term_pair_coexistence_refresh.py
```

target-anchor 语料放在独立组件里。主 corpus 文件只注册 mode 和薄路由。该文件现在约 503 行，后续如果继续扩展，应做 extension dispatcher 拆分，而不是继续增长。

## 新 mode

```text
equals_surface_no_pair_id_target_anchor_repair
```

核心样本：

```text
fixed=fixed
loss=loss
fixed=fixed|loss=loss
loss=loss|fixed=fixed
anchor fixed=fixed
anchor loss=loss
target fixed=fixed
target loss=loss
```

它避免 v579 的自然语言 binding 句，也不回到 first-token rows。

## 真实运行

输出目录：

```text
e/584/解释/model-capability-required-term-pair-target-anchor-seed-3535/
```

结果：

```text
pair_full_seed_count=0
continuation_hit_count=1
```

从 replay CSV 看，`fixed=` 能命中 `fixed`，但 `loss=` 仍倾向生成 `fixed`。

## 测试覆盖

新增测试验证：

- exact equals target rows 的重复数量。
- 包含 anchor/target 形式。
- 不包含 v579 自然语言 binding 句。
- 不引入 numeric pair id。

## 链路角色

v584 是 v583 后的第一条“更强 objective”实验。它没有成功，但相比 v579/v581 恢复了 partial fixed hit，因此需要进入下一版 comparison。

## 一句话总结

v584 用 target-anchor objective 恢复了 partial fixed signal，但仍未解决 loss branch，下一步要和 v571/v579/v581 横向比较。

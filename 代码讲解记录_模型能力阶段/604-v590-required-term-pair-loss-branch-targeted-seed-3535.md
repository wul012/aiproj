# v590 required-term pair loss-branch targeted seed 3535

## 本版目标和边界

v590 是 v589 corpus contract 的第一条真实训练验证。它使用 `equals_surface_no_pair_id_loss_branch_targeted_repair`，在 seed `3535` 上训练 tiny checkpoint，并用现有 generation profile replay 检查 `fixed` 和 `loss` 是否能同时命中。

本版不扩大模型、不换解码策略、不把局部命中当成模型质量提升。它只回答一个问题：targeted loss objective 是否能救回 `loss`，以及是否会牺牲 `fixed`。

## 输入

训练输入来自 v589 新增的 corpus mode：

```text
equals_surface_no_pair_id_loss_branch_targeted_repair
```

关键 corpus 设计：

```text
loss=loss
loss=loss
prompt loss= target loss
loss= should not drift into fixed
fixed=fixed
```

它提高 `loss` 的目标密度，但没有删除 `fixed`，因此可以观察真实 branch tradeoff。

## 运行链路

脚本入口：

```text
scripts/run_model_capability_required_term_pair_coexistence_refresh.py
```

核心模块：

```text
build_model_capability_required_term_pair_coexistence_refresh()
build_model_capability_required_term_pair_generation_profile_replay()
```

流程：

1. 生成 v589 targeted corpus。
2. 调用 `scripts/train.py` 训练 tiny checkpoint。
3. 读取 checkpoint 和 tokenizer。
4. 对 `fixed=`、`loss=` 两个 prompt 做默认和 newline suppression replay。
5. 汇总 pair-full、hit terms、missed terms。

## 关键结果

```text
status=pass
training_status=pass
checkpoint_exists=True
pair_full_observed=False
hit_terms=loss
missed_terms=fixed
```

生成预览显示：

```text
fixed= losssssssss
loss= losssssssss
```

这说明模型已经偏向 `loss`，但没有同时保留 `fixed`。

## 证据链角色

`e/590` 是真实训练证据，不是纯 contract 证据。它提供了第一个 loss-branch objective 的行为边界：能恢复 `loss` residual，但会丢掉 `fixed`。

## 一句话总结

v590 把 loss branch 从设计推入真实训练，结果是 `loss` 被救回、`fixed` 掉线，形成明确的 branch tradeoff。

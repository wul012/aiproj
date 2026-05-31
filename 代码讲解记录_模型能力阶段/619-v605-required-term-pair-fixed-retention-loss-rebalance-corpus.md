# v605 required-term pair fixed-retention loss-rebalance corpus

## 本版目标和边界

v605 承接 v604 route decision：v601 first-token route 能恢复 fixed，但丢失 loss。因此本版新增 loss-rebalance corpus modes。

本版只新增语料和测试，不宣称模型能力提升；真实效果由后续 seed training 验证。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_fixed_retention_loss_rebalance_corpus.py
src/minigpt/model_capability_required_term_pair_coexistence_corpus.py
tests/test_model_capability_required_term_pair_fixed_retention_loss_rebalance_corpus.py
e/605/解释/fixed-retention-loss-rebalance-corpus-contract/
```

## 语料设计

`equals_surface_no_pair_id_fixed_retention_loss_rebalance_repair`：

```text
保留 fixed=f / fixed=fi / fixed=fix / fixed=fixed，同时补 loss=l / loss=lo / loss=los / loss=loss。
```

`equals_surface_no_pair_id_fixed_retention_dual_cycle_repair`：

```text
交替排列 fixed 与 loss 目标，避免单边覆盖。
```

## 测试覆盖

测试确认：

- 两个模式注册进 `PAIR_COEXISTENCE_CORPUS_MODES`。
- 两个模式使用 `fixed=` / `loss=` prompt。
- loss-rebalance 模式同时包含 fixed prefix rows 和 loss rows。
- dual-cycle 模式交替保留两个分支。
- 不引入 `pair=01`。

## 一句话总结

v605 把 fixed-only tradeoff 转化为可训练的 loss-rebalance objective。

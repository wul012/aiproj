# v564 required-term pair no-pair-id loss-balanced first-token stability 代码讲解

## 本版目标和边界

v563 证明 v562 的 missed seeds 主要卡在 first-token ranking。v564 把这个诊断变成一次真实训练实验：在 v561 的 no-pair-id loss-balanced objective 上加入 explicit first-token prefix rows。

本版不扩大模型、不改 decode、不做 held-out。它只验证 first-token prefix rows 是否能把三 seed 稳定性从 v562 的 `1/3` 推高。

## 前置链路

- v561：seed `1535` 单 seed pair-full。
- v562：三 seed 稳定性只有 `1/3`。
- v563：missed seeds 是 first-token gap。

v564 是对 v563 next action 的直接执行。

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_coexistence_corpus.py`
  - 新增 `equals_surface_no_pair_id_loss_balanced_first_token_repair`。
  - 新增 `_extend_equals_surface_no_pair_id_loss_balanced_first_token_repair()`。
  - 文件总行数为 `407`，仍不需要拆分。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 prefix-row 测试。
  - 确认 loss weighting 和 no-pair-id 约束仍成立。
- `e/564/解释/model-capability-required-term-pair-no-pair-id-loss-balanced-first-token-stability/`
  - 保存三 seed 真实训练和 replay 证据。

## 核心语料设计

v564 保留 v561 的主干：

```text
record fixed=fixed loss=loss
record loss=loss fixed=fixed
loss=loss
prompt loss= target loss
```

新增 first-token rows：

```text
fixed=f
fixed=fi
fixed=fix
loss=l
loss=lo
loss=los
first token fixed= f
first token loss= l
```

这组样本是针对 v563 的 first-token ranking gap，而不是继续加 continuation rows。

## 真实结果

三 seed 结果：

```text
535  -> fixed-only
1535 -> pair-full
2535 -> all-miss
```

总体仍是：

```text
pair_full_seed_count=1/3
pair_full_seed_rate=0.3333
stable_pair_full=False
```

v564 相对 v562 有混合变化：seed `535` 有局部改善，但 seed `2535` 退化。因此 explicit prefix rows 不是稳定修复。

## 测试覆盖

新增测试保护：

- prefix rows 确实进入 corpus。
- loss weighting 没被 first-token rows 抹掉。
- `pair=01` 没被重新加入。

收口验证还包括目标测试、全量 pytest、source encoding、`git diff --check` 和 Playwright 截图。

## 归档角色

`e/564` 是 first-token repair 的负/混合证据。它防止项目沿着“继续堆 prefix rows”盲目推进，也为下一版比较 v562/v564 seed 迁移提供输入。

一句话总结：v564 执行了 first-token objective，但稳定性仍停在 `1/3`，下一步应比较 seed 迁移并重新选择修复路线。


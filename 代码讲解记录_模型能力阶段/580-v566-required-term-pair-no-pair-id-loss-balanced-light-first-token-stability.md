# v566 required-term pair no-pair-id loss-balanced light-first-token stability 代码讲解

## 本版目标和边界

v565 证明 full first-token rows 只是把 coverage 从 seed `2535` 迁移到 seed `535`，并没有提高 pair-full。v566 因此尝试更轻的版本：不在 repeat 主体里放 `fixed=f` / `loss=l`，只在 bridge hint 中提醒首 token。

本版不扩大模型、不改 decode、不做 held-out。它只验证 sparse first-token hint 是否能比 v564 更稳。

## 前置链路

- v562：loss-balanced no-pair-id，`1/3` pair-full。
- v564：full first-token rows，仍 `1/3`，但 seed coverage 迁移。
- v565：确认 v564 是 migration，不是净增益。

v566 是对“first-token 是否只需要轻提示”的测试。

## 关键新增和修改文件

- `src/minigpt/model_capability_required_term_pair_coexistence_corpus.py`
  - 新增 `equals_surface_no_pair_id_loss_balanced_light_first_token_repair`。
  - 新增 light hint corpus builder。
  - 文件为 `456` 行，仍低于拆分阈值。
- `tests/test_model_capability_required_term_pair_coexistence_refresh.py`
  - 新增 sparse hint 测试。
  - 确认没有直接 prefix rows。
- `e/566/解释/model-capability-required-term-pair-no-pair-id-loss-balanced-light-first-token-stability/`
  - 保存三 seed 真实训练证据。

## 核心语料设计

v566 保留 v561 主体：

```text
record fixed=fixed loss=loss
record loss=loss fixed=fixed
loss=loss
prompt loss= target loss
```

但 first-token 只放在 bridge hint：

```text
light first token hint fixed= f.
light first token hint loss= l.
```

它不加入：

```text
fixed=f
loss=l
```

这就是 v566 与 v564 的关键区别。

## 真实结果

v566 结果：

```text
pair_full_seed_count=0/3
pair_full_seed_rate=0.0
stable_pair_full=False
```

seed 形态：

```text
535  -> all-miss
1535 -> fixed-only
2535 -> loss-only
```

这比 v562 和 v564 都差。特别是 seed `1535` 的 pair-full 被 light hint 打掉。

## 测试覆盖

新增测试保护：

- light hint 文本存在。
- direct prefix rows 不存在。
- loss weighting 和 no-pair-id 约束仍成立。

完整验证包括目标测试、全量 pytest、source encoding、`git diff --check` 和 Playwright 截图。

## 归档角色

`e/566` 是 first-token hint 密度路线的负证据。它说明“轻一点也许更稳”的假设不成立，后续不应继续围绕 hint 密度微调。

一句话总结：v566 把 sparse first-token hint 排除出候选路线，项目应回到 policy 或更结构化 objective。


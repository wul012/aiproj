# v671 required-term pair dual-boundary corpus

## 本版目标和边界

v671 将 v670 的 plan 变成真实 corpus mode。目标是把 fixed-side repair、loss-side retention、generation anchor、internal anchor 和 stop-naive-resume 边界写入训练语料构造器。

本版不训练模型，不声称能力提升；它是下一版真实训练前的 corpus contract。

## 关键修改

### `src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_corpus.py`

新增 mode：

```text
equals_surface_no_pair_id_loss_internal_explicit_dual_boundary_repair
```

新增 `_extend_explicit_dual_boundary_repair()`，语料包含：

- generation surface rows: 保留 v630 pair-full 形态。
- fixed retention rows: 针对 v669 的 fixed prefix fragment miss。
- loss retention rows: 保留 v667 constrained decode 已恢复的 loss。
- internal rank rows: 继续承接 v640 internal anchor。
- boundary rows: 明确拒绝 naive checkpoint continuation。

## 测试覆盖

更新：

```text
tests/test_model_capability_required_term_pair_coexistence_refresh.py
```

新增测试断言：

- dual boundary surface rows 存在。
- fixed retention rows 存在。
- loss retention rows 存在。
- prefix-fragment-only fixed 被拒绝。
- 修 fixed 时不能抹掉 loss。
- 不含 `pair=01`，避免回到早期 pair-id 干扰。

运行结果：`25 passed`。

## 证据归档

- corpus contract HTML: `e/671/解释/dual-boundary-corpus-contract.html`
- 截图: `e/671/图片/v671-dual-boundary-corpus-contract.png`
- 解释: `e/671/解释/说明.md`

一句话总结：v671 把“显式 dual-objective boundary”从计划变成了可训练的 corpus mode。

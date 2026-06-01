# v643 required-term pair route decision with internal-repair

## 本版目标和边界

v643 消费 v642 comparison，生成新的 route decision。它修复了 route decision 的 anchor 选择：新增的 internal-repair route 比旧的 first-token route 更贴近当前目标，应优先作为 internal anchor。

## 关键修改

```text
src/minigpt/model_capability_required_term_pair_generation_internal_alignment_route_decision.py
tests/test_model_capability_required_term_pair_generation_internal_alignment_route_decision.py
```

`internal_pair_full_generation_none` 现在会优先于 `internal_pair_full_generation_gap` 作为 internal anchor。

## 核心结果

```text
selected_generation_route=loss-internal-joint-cycle
internal_anchor_route=joint-cycle-internal-repair
direct_promotion_ready=False
```

这比 v633/v637 更具体：v641 是当前最强 internal anchor，而不是早期 v621。

## 后续路线

下一版不应继续重跑同一 heavy internal repair，而应做轻量 merge：

```text
generation base: v630 joint-cycle
internal anchor: v641 joint-cycle-internal-repair
target: preserve generation pair-full and keep forced-choice internal full match
```

## 一句话总结

v643 把路线从“修 internal”进一步精确为“用 v641 的 internal anchor 轻量合并到 v630 generation base”。

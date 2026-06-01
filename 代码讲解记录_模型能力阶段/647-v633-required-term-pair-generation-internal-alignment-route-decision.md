# v633 required-term pair generation/internal alignment route decision

## 本版目标和边界

v633 消费 v632 的 alignment comparison，输出机器可读路线决策。它的目标是把“下一步怎么做”从文字判断变成可复核 artifact。

本版不训练模型，不新增 corpus mode，也不做 promotion。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_generation_internal_alignment_route_decision.py
src/minigpt/model_capability_required_term_pair_generation_internal_alignment_route_decision_artifacts.py
scripts/run_model_capability_required_term_pair_generation_internal_alignment_route_decision.py
tests/test_model_capability_required_term_pair_generation_internal_alignment_route_decision.py
e/633/解释/model-capability-required-term-pair-generation-internal-alignment-route-decision/
```

## 输入输出

输入是 v632 comparison JSON：

```text
model_capability_required_term_pair_generation_internal_alignment_comparison.json
```

输出包含 route decision 的 JSON/CSV/text/Markdown/HTML。JSON 中保留：

```text
selected_generation_route
internal_anchor_route
aligned_route
constraints
summary
interpretation
```

## 核心决策

真实运行结果：

```text
decision=repair_internal_preference_preserve_generation_pair_full
selected_generation_route=loss-internal-joint-cycle
internal_anchor_route=loss-internal-first-token
direct_promotion_ready=False
```

含义是：

- v630 joint-cycle 作为下一步训练 base，因为它已经 generation pair-full。
- v621 first-token 作为 internal anchor，因为它 forced-choice full match。
- 由于 aligned route 为空，不能 promotion。

## 约束语义

`preserve_generation_pair_full`：后续目标不能牺牲 v630 的 fixed/loss 生成双命中。

`repair_loss_internal_preference`：后续目标要修复 v631 中 `loss=` 内部仍偏 fixed 的问题。

`avoid_pair_id_shortcut`：继续避免显式 pair id 泄漏，防止模型记住编号而非学到提示到 term 的映射。

## 测试覆盖

单测覆盖三类情形：

- generation route + internal anchor 同时存在时，选择 repair route。
- aligned candidate 存在时，进入 repeat-before-promotion。
- route decision 的五种输出格式可生成。

## 一句话总结

v633 把 v630/v631 的能力状态收束成下一版训练约束：保 generation，补 internal，暂不 promotion。

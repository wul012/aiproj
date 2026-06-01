# v625 required-term pair loss-internal-preference route decision

## 本版目标和边界

v625 是 v623/v624 之后的路线决策。它回答一个关键问题：v621 有内部 pair match，但生成 replay 不是 pair-full，那么它能不能 promotion？

本版结论是不能 promotion，只能作为 decode bridge 候选。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_internal_preference_route_decision.py
src/minigpt/model_capability_required_term_pair_loss_internal_preference_route_decision_artifacts.py
scripts/run_model_capability_required_term_pair_loss_internal_preference_route_decision.py
tests/test_model_capability_required_term_pair_loss_internal_preference_route_decision.py
```

## 输入输出

输入：

```text
e/623/解释/model-capability-required-term-pair-loss-internal-preference-objective-comparison/
e/624/解释/model-capability-required-term-pair-loss-internal-forced-choice-diagnostic/
```

输出：

```text
e/625/解释/model-capability-required-term-pair-loss-internal-preference-route-decision/
e/625/图片/v625-loss-internal-preference-route-decision.png
```

## 核心字段

`route_rows` 同时记录：

- generation 是否 pair-full。
- forced-choice 是否 pair-full。
- 是否是 decode bridge candidate。
- 为什么不能 promotion。

`summary.selected_decode_bridge_source` 选择 v621 的 `loss-internal-first-token`。

## 决策结果

```text
decision=select_loss_internal_first_token_for_decode_bridge_not_promotion
selected_decode_bridge_source=loss-internal-first-token
internal_to_generation_bridge_required=True
```

这说明下一步要研究 decoding/generation path，而不是继续无差别加 objective。

## 测试覆盖

新增测试覆盖：

- 内部 pair match 但 generation 非 pair-full 时选择 decode bridge。
- forced-choice 没有 internal match 时失败。
- JSON/CSV/text/Markdown/HTML 输出可生成。

## 一句话总结

v625 把 v621 定位为“内部偏好已出现但生成未释放”的 decode bridge 候选。

# v626 required-term pair loss-internal decode bridge check

## 本版目标和边界

v626 检查 v625 选中的 v621 first-token route：它内部已经 pair match，但生成没有 pair-full。这个版本要回答“桥接缺口具体是哪一个 term”。

本版不训练模型，也不设计新语料；它只给 v627 的 bridge corpus 提供约束。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_internal_decode_bridge_check.py
src/minigpt/model_capability_required_term_pair_loss_internal_decode_bridge_check_artifacts.py
scripts/run_model_capability_required_term_pair_loss_internal_decode_bridge_check.py
tests/test_model_capability_required_term_pair_loss_internal_decode_bridge_check.py
```

## 输入输出

输入：

```text
e/621/解释/model-capability-required-term-pair-loss-internal-first-token-seed-3535/
e/624/解释/model-capability-required-term-pair-loss-internal-forced-choice-diagnostic/
e/625/解释/model-capability-required-term-pair-loss-internal-preference-route-decision/
```

输出：

```text
e/626/解释/model-capability-required-term-pair-loss-internal-decode-bridge-check/
e/626/图片/v626-loss-internal-decode-bridge-check.png
```

## 核心字段

`bridge_rows` 按 term 对齐两类证据：

- `generation_hit`
- `forced_choice_expected_best`
- `bridge_gap`

如果内部 expected-best 为真，但 generation 未命中，就形成 bridge gap。

## 运行结果

```text
generation_hit_terms=loss
forced_choice_expected_best_terms=fixed,loss
bridge_gap_terms=fixed
decode_bridge_ready=True
```

这说明 v627 不应该继续强化 loss，而应该在保留 loss 的前提下恢复 fixed generation。

## 测试覆盖

新增测试覆盖：

- 内部 pair match 且 generation 缺 fixed 时，确认 bridge gap。
- 如果 generation 已经 pair-full，则 check 失败，避免无意义 bridge。
- JSON/CSV/text/Markdown/HTML 输出可生成。

## 一句话总结

v626 把“内部偏好到生成”的问题定位为 fixed generation bridge gap。

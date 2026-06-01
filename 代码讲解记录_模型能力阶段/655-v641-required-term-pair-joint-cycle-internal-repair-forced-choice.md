# v641 required-term pair joint-cycle internal-repair forced-choice

## 本版目标和边界

v641 检查 v640 checkpoint 的内部偏好。v640 在 generation replay 中失败，但 forced-choice 可以判断 internal repair 是否有局部收益。

本版不训练模型，只读 v640 checkpoint。

## 输入输出

输入：

```text
e/640/解释/model-capability-required-term-pair-joint-cycle-internal-repair-seed-3535/
```

输出：

```text
e/641/解释/model-capability-required-term-pair-joint-cycle-internal-repair-forced-choice/
e/641/图片/v641-joint-cycle-internal-repair-forced-choice.png
```

## 核心结果

```text
decision=refresh_forced_choice_internal_pair_match
expected_best_prompt_count=2
forced_choice_full_match_source_count=1
```

prompt summaries：

```text
fixed= -> fixed is best
loss=  -> loss is best
```

这说明 v639 corpus 的 internal 部分是有效的，只是它破坏了 generation surface。

## 链路角色

v641 让后续路线更清晰：不是简单抛弃 internal-repair，而是要把 v630 的 generation surface 和 v641 的 internal preference 对齐到同一个 checkpoint。

## 一句话总结

v641 证明 internal repair 生效，但 generation/internal 仍然分裂。

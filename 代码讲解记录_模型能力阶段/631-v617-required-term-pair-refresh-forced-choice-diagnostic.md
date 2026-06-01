# v617 required-term pair refresh forced-choice diagnostic

## 本版目标和边界

v617 跑 v616 新增的 forced-choice diagnostic，读取 v611-v613 的真实 checkpoint，比较 `fixed=` / `loss=` 下 `fixed` 与 `loss` 的 teacher-forced NLL。

本版不训练，不改语料，不声明模型能力提升；它只解释“为什么采样仍偏 fixed”。

## 输入输出

输入：

```text
e/611/解释/model-capability-required-term-pair-contrast-free-seed-3535/
e/612/解释/model-capability-required-term-pair-delimiter-span-seed-3535/
e/613/解释/model-capability-required-term-pair-context-switch-seed-3535/
```

输出：

```text
e/617/解释/model-capability-required-term-pair-refresh-forced-choice-diagnostic/
```

## 核心结果

```text
status=pass
decision=refresh_forced_choice_partial_internal_match
expected_best_prompt_count=3
forced_choice_full_match_source_count=0
```

每个 checkpoint 的 `fixed=` prompt 都内部偏好 `fixed`；每个 `loss=` prompt 也内部偏好 `fixed`。这与 v612/v613 的采样结果一致。

## 证据意义

v617 把问题从“生成时漂移”推进到“模型内部偏好”。如果 teacher-forced 比较里 `loss` 也不是最佳候选，那么继续调 decoding 参数没有意义。

## 一句话总结

v617 证明 contrast-free batch 的内部偏好仍然固定在 fixed branch，下一步应结束本批路线。

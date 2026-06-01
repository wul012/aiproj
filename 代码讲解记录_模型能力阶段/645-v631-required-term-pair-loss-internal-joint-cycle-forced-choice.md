# v631 required-term pair loss-internal joint-cycle forced-choice

## 本版目标和边界

v631 检查 v630 checkpoint 的内部偏好。v630 已经生成 pair-full，但 forced-choice 可以回答另一个问题：当候选答案固定为 fixed/loss 时，模型内部负对数似然是否也更偏向正确答案。

本版不改变模型和语料，只读 v630 checkpoint 并生成 sidecar 诊断。

## 输入和输出

输入：

```text
e/630/解释/model-capability-required-term-pair-loss-internal-joint-cycle-seed-3535/
```

输出：

```text
e/631/解释/model-capability-required-term-pair-loss-internal-joint-cycle-forced-choice/
e/631/图片/v631-loss-internal-joint-cycle-forced-choice.png
```

## 核心结果

```text
decision=refresh_forced_choice_partial_internal_match
expected_best_prompt_count=1
forced_choice_full_match_source_count=0
```

prompt summaries：

```text
fixed= -> fixed is best
loss=  -> fixed is best, loss is not best
```

这说明 v630 的 pair-full 是生成层可见的正结果，但内部 forced-choice 还没有同步变成 fixed/loss full match。

## 链路角色

v631 的价值在于防止过早 promotion。它把能力状态拆成两层：

- generation pair-full：v630 已满足。
- internal pair-full：v631 未满足。

后续版本应比较 v621、v628、v630 这几条路线，明确哪个候选更适合继续训练。

## 测试和证据

本版复用 v616 引入的 forced-choice diagnostic CLI。HTML 截图和 JSON 都证明 `Full match=0`，因此 README 不会把 v630 错写成“稳定 pair 能力”。

## 一句话总结

v631 证明 v630 是重要但不完整的正结果：生成 pair-full 已出现，内部偏好仍需继续对齐。

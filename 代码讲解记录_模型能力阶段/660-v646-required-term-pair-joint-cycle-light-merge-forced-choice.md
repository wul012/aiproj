# v646 required-term pair joint-cycle light-merge forced-choice

## 本版目标和边界

v646 检查 v645 light-merge checkpoint 的内部偏好。v645 生成层偏 loss，本版确认 internal 是否也跟随 loss。

本版只读 checkpoint，不做训练。

## 输入输出

输入：

```text
e/645/解释/model-capability-required-term-pair-joint-cycle-light-merge-seed-3535/
```

输出：

```text
e/646/解释/model-capability-required-term-pair-joint-cycle-light-merge-forced-choice/
e/646/图片/v646-joint-cycle-light-merge-forced-choice.png
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

这说明 light-merge 没有带来 internal pair-full。

## 证据意义

v646 让 v645 的结果更明确：它不是 aligned route，而是 generation 和 internal 继续错位。

## 一句话总结

v646 证明 light-merge 没有成为解法，下一步应做全路线 closeout。

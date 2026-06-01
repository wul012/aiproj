# v635 required-term pair loss-internal balanced-anchor forced-choice

## 本版目标和边界

v635 对 v634 balanced-anchor checkpoint 做 teacher-forced forced-choice 诊断。它不训练模型，只检查内部偏好是否和生成层一样偏 fixed。

## 输入和输出

输入：

```text
e/634/解释/model-capability-required-term-pair-loss-internal-balanced-anchor-seed-3535/
```

输出：

```text
e/635/解释/model-capability-required-term-pair-loss-internal-balanced-anchor-forced-choice/
e/635/图片/v635-loss-internal-balanced-anchor-forced-choice.png
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

这说明 balanced-anchor 没有形成 loss-side internal preference。

## 链路角色

v635 与 v634 一起构成完整负结果：generation 和 internal 两个层面都没有超过 v630 joint-cycle。

## 一句话总结

v635 确认 balanced-anchor 不是 alignment 修复方向，下一步应把它纳入比较后继续围绕 v630 修 internal。

# v614 required-term pair contrast-free objective comparison

## 本版目标和边界

v614 读取 v611-v613 的真实训练报告，比较三条新 objective route 的 branch 覆盖情况。它不训练新模型，只做机器可读比较。

## 输入输出

输入：

```text
e/611/解释/model-capability-required-term-pair-contrast-free-seed-3535/
e/612/解释/model-capability-required-term-pair-delimiter-span-seed-3535/
e/613/解释/model-capability-required-term-pair-context-switch-seed-3535/
```

输出：

```text
e/614/解释/model-capability-required-term-pair-contrast-free-objective-comparison/
```

## 核心结果

```text
status=pass
decision=select_fixed_retention_route_for_loss_rebalance
pair_full_report_count=0
fixed_only_tradeoff_report_count=2
loss_only_tradeoff_report_count=0
union_hit_terms=fixed
fixed_recovery_route=v612-delimiter-span
```

`union_hit_terms=fixed` 是最重要结论：新 objective batch 没有恢复 loss，只是把部分 route 推向 fixed。

## 证据边界

比较器的默认 decision 会说 `select_fixed_retention_route_for_loss_rebalance`，但结合 v608 closeout，这个建议不能机械执行。v615 需要在 route decision 中把 v608/v609 的历史约束纳入，避免重复做已经失败的 loss-rebalance 分支。

## 一句话总结

v614 证明三条 contrast-free objective route 没有 pair-full，只产生 fixed-only 恢复信号。

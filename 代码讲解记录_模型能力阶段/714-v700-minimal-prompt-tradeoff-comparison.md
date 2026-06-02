# v700 minimal prompt tradeoff comparison

## 本版目标和边界

v700 的目标是对比 v696 和 v699，而不是继续训练。它复用已有 `first_token_preference_diagnostic`，把两个真实 refresh report 放在同一个报告中。

本版不新增代码，不新增 corpus mode，不做模型能力 claim。它是对照诊断版。

## 前置链路

v696：

```text
corpus_mode=minimal_prompt_equals_surface_objective
fixed= hit
loss= miss into fixed
```

v699：

```text
corpus_mode=minimal_prompt_loss_first_token_repair_objective
loss= hit
fixed= miss into loss
```

v700 检查这两者是否构成 first-token preference tradeoff。

## 复用工具

使用脚本：

```text
scripts/run_model_capability_required_term_pair_first_token_preference_diagnostic.py
```

这个脚本要求至少两个 refresh report，正好适合 v696/v699。

## 关键输出

```text
decision=first_token_preference_tradeoff_confirmed
source_report_count=2
first_token_conflict_confirmed=True
mixed_branch_tradeoff_confirmed=True
other_term_start_count=4
model_quality_claim=diagnostic_only
```

含义：

- 两个 report 都有效。
- 有 prompt 以竞争 term 开头。
- 一个 report fixed-only，另一个 report loss-only。
- 没有 pair-full 候选。

## 运行证据

证据目录：

```text
e/700/解释/model-capability-required-term-pair-minimal-prompt-tradeoff-comparison/
e/700/图片/v700-minimal-prompt-tradeoff-comparison.png
```

## 下一步

下一版不应继续单边 loss-first-token 或 fixed-first-token。更合适的是设计 balanced repair：

- 同时保留 fixed 和 loss direct rows。
- 避免 contextual anchor。
- 用对称 first-token rows 控制两边分支。
- 再用同 seed `3535` 真实训练验证。

## 一句话总结

v700 证明 minimal-prompt 当前问题是 first-token tradeoff，而不是简单缺少某一侧训练样本。

# v582 required-term pair branch-binding comparison

## 本版目标和边界

v582 横向比较三条 seed `3535` 路线：

```text
v571-loss-balanced
v579-branch-binding
v581-branch-binding-no-space
```

目标是判断 v579/v581 是否比旧路线更有价值。本版不训练、不改模型、不新增 corpus。它只读已有报告，避免因为连续负结果而继续凭感觉加语料。

## 输入输出

输入：

```text
e/571/解释/model-capability-required-term-pair-route-fresh-seed-3535/
e/579/解释/model-capability-required-term-pair-branch-binding-seed-3535/
e/581/解释/model-capability-required-term-pair-branch-binding-no-space-seed-3535/
```

输出：

```text
e/582/解释/model-capability-required-term-pair-branch-binding-comparison/
```

## 核心结果

```text
pair_full_profile_seed_count=0
union_hit_terms=fixed
fixed_hit_reports=v571-loss-balanced
loss_hit_reports=[]
```

这说明三条路线都没有 pair-full；只有 v571 还保留了 fixed partial hit，v579/v581 连 partial visible term 都没有。

## 证据解释

v579 的自然语言 branch-binding 被 v580 诊断为 whitespace first-token gap。

v581 移除了会诱导 whitespace 的自然语言句子，但训练结果仍然没有 visible hit。

v582 因此不是选择一个“最好”的成功路线，而是确认：

```text
branch-binding v1/v2 当前不如 v571 baseline。
```

## 验证方式

本版复用 `run_model_capability_required_term_pair_equals_surface_repair_comparison.py`。验证点：

- 三份输入报告都能读取。
- comparison `status=pass`。
- Playwright MCP 截图证明 HTML comparison 可见。

## 链路角色

v582 是 branch-binding route 的分叉判断。它阻止我们继续对 v579/v581 做小修小补，除非下一版能明确提出更强的 objective。

## 一句话总结

v582 证明 branch-binding v1/v2 相对 v571 是回退路线，下一步应该用 route decision 停止这两个变体或设计更强约束。

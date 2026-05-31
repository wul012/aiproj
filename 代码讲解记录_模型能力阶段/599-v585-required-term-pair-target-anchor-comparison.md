# v585 required-term pair target-anchor comparison

## 本版目标和边界

v585 比较 v571、v579、v581、v584 四条 fresh-seed `3535` 路线。目标是判断 v584 target-anchor 是否真正超过 v571 residual baseline。

本版不训练、不改代码、不扩大模型。它只读已有真实训练报告。

## 输入输出

输入：

```text
e/571/解释/model-capability-required-term-pair-route-fresh-seed-3535/
e/579/解释/model-capability-required-term-pair-branch-binding-seed-3535/
e/581/解释/model-capability-required-term-pair-branch-binding-no-space-seed-3535/
e/584/解释/model-capability-required-term-pair-target-anchor-seed-3535/
```

输出：

```text
e/585/解释/model-capability-required-term-pair-target-anchor-comparison/
```

## 核心结果

```text
compared_report_count=4
pair_full_profile_seed_count=0
union_hit_terms=fixed
fixed_hit_reports=v571-loss-balanced,v584-target-anchor
loss_hit_reports=
```

v579/v581 没有 visible hit；v571/v584 都只有 fixed partial hit；没有任何路线命中 loss。

## 证据解释

v584 target-anchor 是有价值的，因为它从 v579/v581 的零 visible hit 回到了 partial fixed。

但它没有超过 v571，因为：

- 没有 pair-full。
- 没有 loss hit。
- `union_hit_terms` 仍然只有 `fixed`。

因此 v584 是 residual candidate，不是 promotion candidate。

## 验证方式

本版复用 equals-surface repair comparison。验证点：

- 四份输入都成功读取。
- comparison `status=pass`。
- Playwright MCP 截图证明 HTML 报告可见。

## 链路角色

v585 为后续 route decision 提供依据：branch-binding v1/v2 应停止，target-anchor 可保留为 residual candidate，但下一步核心仍是 loss branch objective。

## 一句话总结

v585 证明 target-anchor 只恢复了 v571 级别的 fixed partial signal，尚未解决 loss branch。

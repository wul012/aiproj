# v576 required-term pair route fresh seed 3535 variable comparison

## 本版目标和边界

v576 是 seed `3535` 的变量实验收口。v571、v573、v575 都是真实训练，但分别只代表一个变量。v576 把它们统一比较，回答哪条已试变量更值得继续。

这一版不训练、不改代码，只读归档报告。

## 输入报告

```text
v571-loss-balanced
e/571/解释/model-capability-required-term-pair-route-fresh-seed-3535/

v573-first-token
e/573/解释/model-capability-required-term-pair-route-fresh-seed-3535-first-token-repair/

v575-wider-embd
e/575/解释/model-capability-required-term-pair-route-fresh-seed-3535-wider-embd/
```

## 输出报告

```text
e/576/解释/model-capability-required-term-pair-route-fresh-seed-3535-variable-comparison/
```

## 核心字段

```text
compared_report_count=3
pair_full_profile_seed_count=0
union_hit_terms=fixed
```

`union_hit_terms=fixed` 表示三条路线合起来也没有让 `loss` 成为 visible hit。fresh seed `3535` 的核心问题仍然是 loss branch 绑定失败。

## 证据解读

- v571 保留了 fixed partial hit。
- v573 的 first-token rows 没有修复 loss，反而丢掉 visible hit。
- v575 的 wider embedding 也没有修复 loss，且同样没有 visible hit。

因此，已试变量的排序不是“谁最好”，而是：

```text
都不是可推广修复；v571 只是保留了最多残余信号。
```

## 验证方式

本版复用 equals-surface repair comparison 脚本。验证点：

- 三份输入都成功读取。
- comparison `status=pass`。
- Playwright 截图证明 HTML summary 和 term rows 可见。

## 链路角色

v576 把 v571-v575 变成一个停止信号：不要继续沿 first-token rows 或 width scaling 做小变体，应该先产出路线决策或设计新的 objective。

## 一句话总结

v576 证明 seed 3535 的 fresh-seed 问题没有被已有 first-token repair 或宽度提升解决，下一步应停止这两个变量方向。

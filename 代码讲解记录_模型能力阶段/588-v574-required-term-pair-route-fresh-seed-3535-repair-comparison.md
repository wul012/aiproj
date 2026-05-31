# v574 required-term pair route fresh seed 3535 repair comparison

## 本版目标和边界

v574 对比 v571 和 v573。v571 是 fresh seed `3535` 的 loss-balanced route；v573 是同一 seed 的 full first-token repair route。两个版本都失败，但失败程度不同。v574 把它们统一到 comparison artifact 中。

这一版不训练、不改代码，只做证据收束。

## 输入报告

```text
v571-loss-balanced-fresh3535
e/571/解释/model-capability-required-term-pair-route-fresh-seed-3535/

v573-first-token-fresh3535
e/573/解释/model-capability-required-term-pair-route-fresh-seed-3535-first-token-repair/
```

## 输出报告

```text
e/574/解释/model-capability-required-term-pair-route-fresh-seed-3535-repair-comparison/
```

主文件：

- `model_capability_required_term_pair_equals_surface_repair_comparison.json`
- `model_capability_required_term_pair_equals_surface_repair_comparison.csv`
- `model_capability_required_term_pair_equals_surface_repair_comparison.html`

## 核心字段

```text
compared_report_count=2
term_case_row_count=8
pair_full_profile_seed_count=0
union_hit_terms=fixed
```

`union_hit_terms=fixed` 很关键：两条路线合起来也只看到 fixed hit，没有看到 loss hit。也就是说 v573 的 first-token repair 没有修复 loss branch。

## 证据解读

v571 至少保留了一个 fixed partial signal。v573 使用 full first-token rows 后没有 pair-full，也没有 visible continuation hit。它不是“还不够强”，而是在这个 seed 上比 v571 更差。

## 测试和验证

本版复用 v555/v567 使用过的 equals-surface comparison 脚本。验证重点：

- comparison CLI `status=pass`。
- 两份输入都被识别为 equals-surface corpus mode。
- HTML 报告通过 Playwright 截图归档。

## 链路角色

v574 是决策前的对比层。它阻止我们继续沿用 v573 的 first-token rows 做 fresh-seed 修复，把下一步导向更窄的 loss-branch 诊断或更结构化 objective。

## 一句话总结

v574 证明 seed 3535 上的 full first-token repair 是退化路线，后续不应把它作为 fresh-seed 修复主线。

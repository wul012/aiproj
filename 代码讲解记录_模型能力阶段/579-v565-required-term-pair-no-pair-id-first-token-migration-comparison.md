# v565 required-term pair no-pair-id first-token migration comparison 代码讲解

## 本版目标和边界

v564 加入 first-token rows 后没有提升三 seed pair-full，仍然是 `1/3`。v565 的目标是把 v562 与 v564 放在一起，判断 first-token rows 是“净增益”还是“覆盖迁移”。

本版不训练、不改代码、不新增 corpus。它只读两个已归档 stability report。

## 前置链路

- v562：loss-balanced no-pair-id，`1/3` pair-full，seed `2535` loss-only。
- v564：first-token rows，仍 `1/3` pair-full，seed `535` fixed-only，seed `2535` all-miss。

v565 是对这两个实验的对比解释层。

## 关键文件

- `scripts/run_model_capability_required_term_pair_equals_surface_repair_comparison.py`
  - 既有 comparison CLI。
- `e/565/解释/model-capability-required-term-pair-no-pair-id-first-token-migration-comparison/`
  - 保存 comparison JSON、CSV、text、Markdown、HTML 和 Playwright snapshot。
- `e/565/图片/01-model-capability-required-term-pair-no-pair-id-first-token-migration-comparison.png`
  - HTML comparison 截图。

## 输入输出格式

输入是两个 stability 目录：

```text
e/562/解释/model-capability-required-term-pair-equals-surface-no-pair-id-loss-balanced-stability
e/564/解释/model-capability-required-term-pair-no-pair-id-loss-balanced-first-token-stability
```

输出主报告包含：

- `source_reports`
- `branch_rows`
- `term_rows`
- `summary`
- `interpretation`

其中 `branch_rows` 是本版最关键的数据。

## 真实结果

seed-level branch rows 显示：

```text
1535 -> fixed/loss in v562 and v564; pair-full in both
2535 -> loss only in v562; all-miss in v564
535  -> all-miss in v562; fixed only in v564
```

因此 v564 的 prefix rows 不是稳定提升。它让 seed `535` 获得 fixed，但让 seed `2535` 失去 loss，总 pair-full 没变。

## 边界说明

comparison report 的通用 `next_action` 会写出“promote held-out replay”之类的提示，但在 v562/v564 的上下文里，这个提示过于乐观。人工解释应以 branch rows 为准：两个候选都只有 `1/3` pair-full，不能 promotion 为稳定 objective baseline。

## 验证和归档角色

本版没有新增代码，验证重点是：

- comparison CLI 能读取两个归档报告。
- CSV/JSON/HTML 输出完整。
- Playwright 能打开 HTML 并截图。
- 后续收口仍跑全量 pytest、source encoding 和 `git diff --check`。

一句话总结：v565 证明 first-token rows 带来的是 coverage 迁移而非稳定增益，下一步应转向 objective mix 或 seed/config policy。


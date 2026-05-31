# v562 required-term pair equals-surface no-pair-id loss-balanced stability 代码讲解

## 本版目标和边界

v561 恢复了 seed `1535` 的 fixed/loss pair-full，但单 seed 成功不能证明目标已经稳定。v562 因此不改代码、不改语料模式，直接把 v561 objective 扩到 seeds `535,1535,2535`。

本版不做新 corpus、不做 held-out，也不扩大模型。它只验证 v561 的 loss-balanced no-pair-id 目标是否跨 seed 稳定。

## 前置链路

- v560：no-pair-id 让 `fixed=` 恢复，但 `loss=` 失败。
- v561：loss-balanced no-pair-id 让 seed `1535` 达到 pair-full。

v562 是 v561 的稳定性门槛，防止项目把单 seed 修复误判成通用基线。

## 关键文件

- `e/562/解释/model-capability-required-term-pair-equals-surface-no-pair-id-loss-balanced-stability/model_capability_required_term_pair_colon_immediate_stability.json`
  - 三 seed 稳定性主报告。
- `e/562/解释/model-capability-required-term-pair-equals-surface-no-pair-id-loss-balanced-stability/seed-runs/`
  - seeds `535`、`1535`、`2535` 的真实训练输出。
- `e/562/解释/model-capability-required-term-pair-equals-surface-no-pair-id-loss-balanced-stability/seed-reports/`
  - 每个 seed 的 replay 报告。
- `e/562/图片/01-model-capability-required-term-pair-equals-surface-no-pair-id-loss-balanced-stability.png`
  - Playwright 截图。

## 输入输出格式

输入保持 v561 的 corpus mode：

```text
corpus_mode=equals_surface_no_pair_id_loss_balanced_repair
seeds=535,1535,2535
n_embd=64
top_k=2
temperature=0.8
```

主报告汇总：

```json
{
  "decision": "required_term_pair_colon_immediate_partial_stability",
  "summary": {
    "seed_count": 3,
    "pair_full_seed_count": 1,
    "pair_full_seed_rate": 0.3333,
    "stable_pair_full": false
  }
}
```

## 真实结果

三个 seed 的结果是：

```text
535  -> pair_full=False, default/suppression hit count 0
1535 -> pair_full=True,  default/suppression hit count 2
2535 -> pair_full=False, default/suppression hit count 1
```

这说明 v561 的目标确实修好了 seed `1535`，但没有形成稳定基线。尤其 seed `535` 是全 miss，seed `2535` 仍保留 loss-only 偏置。

## 测试和验证角色

本版没有新增 Python 代码，因此核心验证是：

- runner 能完成三 seed 真实训练。
- 每个 seed 的 checkpoint、report、replay evidence 都被归档。
- Playwright 能打开 HTML 报告。
- 后续收口仍需要全量 pytest、source encoding 和 `git diff --check`。

## 归档角色

`e/562` 是 v561 positive signal 的稳定性约束证据。它保护项目不会把 `1/1` 单 seed 结果直接升级为模型能力结论。

一句话总结：v562 证明 loss-balanced no-pair-id 目标只恢复了 seed `1535`，下一步应诊断 missed seeds 后再决定是否继续调语料或参数。


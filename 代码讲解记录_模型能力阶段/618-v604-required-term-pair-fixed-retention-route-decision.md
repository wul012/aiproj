# v604 required-term pair fixed-retention route decision

## 本版目标和边界

v604 新增 fixed-retention route decision。它承接 v603 comparison，不训练模型，只负责把比较结果转为下一步路线。

本版明确不做 promotion：因为没有任何 route 达到 pair-full。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_fixed_retention_route_decision.py
src/minigpt/model_capability_required_term_pair_fixed_retention_route_decision_artifacts.py
scripts/run_model_capability_required_term_pair_fixed_retention_route_decision.py
tests/test_model_capability_required_term_pair_fixed_retention_route_decision.py
e/604/解释/model-capability-required-term-pair-fixed-retention-route-decision/
```

## 核心判断

输入来自 v603：

```text
pair_full_report_count=0
fixed_only_tradeoff_report_count=1
loss_only_tradeoff_report_count=2
fixed_recovery_route=v601-first-token
```

v604 输出：

```text
decision=select_fixed_recovery_route_for_loss_rebalance_not_promotion
loss_rebalance_objective_required=True
```

## 数据结构

`route_rows` 保留每条 route 的：

```text
source_label
route_type
corpus_mode
hit_terms
missed_terms
pair_full_observed
```

`summary` 则记录 selected route 与是否需要 loss rebalance。

## 测试覆盖

测试覆盖：

- mixed tradeoff 时选择 v601 first-token route。
- pair-full route 出现时转为 promotion candidate。
- JSON/CSV/TXT/Markdown/HTML 全格式输出。
- CLI 支持 comparison 目录输入。

## 一句话总结

v604 将 fixed-retention 路线从“比较结果”推进到“loss-rebalance 下一步决策”。

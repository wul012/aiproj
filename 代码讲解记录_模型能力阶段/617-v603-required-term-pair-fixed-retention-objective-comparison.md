# v603 required-term pair fixed-retention objective comparison

## 本版目标和边界

v603 新增 fixed-retention objective comparison，把 v600-v602 的三个真实训练报告放到同一张证据表里。它不训练模型，也不做 promotion；它只判断哪些 route 有可用信号。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_fixed_retention_objective_comparison.py
src/minigpt/model_capability_required_term_pair_fixed_retention_objective_comparison_artifacts.py
scripts/run_model_capability_required_term_pair_fixed_retention_objective_comparison.py
tests/test_model_capability_required_term_pair_fixed_retention_objective_comparison.py
e/603/解释/model-capability-required-term-pair-fixed-retention-objective-comparison/
```

## 核心字段

`branch_rows` 记录每条 route 的命中项：

```text
source_label
corpus_mode
hit_terms
missed_terms
pair_full_profiles
fixed_only_tradeoff
loss_only_tradeoff
```

`summary` 汇总：

```text
pair_full_report_count=0
fixed_only_tradeoff_report_count=1
loss_only_tradeoff_report_count=2
fixed_recovery_route=v601-first-token
```

## 运行流程

CLI 接收 v600-v602 的 coexistence refresh 输出目录：

```text
scripts/run_model_capability_required_term_pair_fixed_retention_objective_comparison.py
```

它会定位每个目录下的 `model_capability_required_term_pair_coexistence_refresh.json`，读取 replay case rows，并判断每条 route 命中了 `fixed`、`loss` 还是两者。

## 测试覆盖

测试覆盖：

- fixed-only 与 loss-only 同时存在时 comparison pass。
- 有 pair-full route 时切到 promotion candidate。
- 非 fixed-retention corpus mode 会失败。
- JSON/CSV/TXT/Markdown/HTML 全格式输出。
- CLI 支持目录输入。

## 一句话总结

v603 把 v600-v602 的零散训练结果收敛为明确判断：v601 是 fixed recovery route，但仍需 loss rebalance。

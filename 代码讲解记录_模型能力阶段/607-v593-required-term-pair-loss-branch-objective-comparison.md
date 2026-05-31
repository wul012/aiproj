# v593 required-term pair loss-branch objective comparison

## 本版目标和边界

v593 对 v590-v592 三条真实训练结果做结构化比较。旧的 equals-surface comparison 主要面向多 seed stability 报告，而 v590-v592 是单次 `coexistence_refresh` 报告；因此本版新增一个专门读取 refresh report 的 comparison 模块。

本版不训练模型，不修改 corpus，也不做 promotion。它只把三条路线的真实结果统一成一个可复核的 route-level 判断。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_branch_objective_comparison.py
src/minigpt/model_capability_required_term_pair_loss_branch_objective_comparison_artifacts.py
scripts/run_model_capability_required_term_pair_loss_branch_objective_comparison.py
tests/test_model_capability_required_term_pair_loss_branch_objective_comparison.py
e/593/解释/model-capability-required-term-pair-loss-branch-objective-comparison/
```

## 输入输出

输入是 v590-v592 的 refresh 输出目录：

```text
e/590/解释/model-capability-required-term-pair-loss-branch-targeted-seed-3535
e/591/解释/model-capability-required-term-pair-loss-branch-dual-anchor-seed-3535
e/592/解释/model-capability-required-term-pair-loss-branch-micro-span-seed-3535
```

模块会自动定位：

```text
model_capability_required_term_pair_coexistence_refresh.json
```

输出包括 JSON、CSV、TXT、Markdown、HTML。

## 核心数据结构

`source_reports` 记录每个输入 report 的结构状态：

```text
source_label
corpus_mode
seed
training_status
checkpoint_exists
pair_full_observed
```

`term_rows` 从 replay case rows 提取固定字段：

```text
term
prompt
profile_id
continuation_hit
generated_preview
continuation_preview
```

`branch_rows` 汇总每条路线的命中情况：

```text
hit_terms
missed_terms
loss_only_tradeoff
fixed_only_tradeoff
pair_full_observed
```

## 关键结论

```text
decision=loss_branch_objectives_confirm_loss_only_tradeoff
compared_report_count=3
pair_full_report_count=0
loss_only_tradeoff_report_count=3
union_hit_terms=loss
```

这说明三条 objective 都能恢复 `loss`，但都不能保留 `fixed`。

## 测试覆盖

新增测试覆盖：

- 三个 loss-only report 会得到 `loss_branch_objectives_confirm_loss_only_tradeoff`。
- 一旦出现 pair-full report，会得到 promotion candidate。
- 非 loss-branch corpus mode 会失败。
- CLI 在 `--require-pass` 下遇到坏输入返回非零。
- JSON/CSV/TXT/Markdown/HTML 都能生成。

## 一句话总结

v593 把三条真实 loss-branch 训练从“现象相似”升级为“结构化确认：全部是 loss-only tradeoff”。

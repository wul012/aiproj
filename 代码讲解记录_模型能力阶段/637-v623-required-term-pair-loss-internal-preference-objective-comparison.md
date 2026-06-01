# v623 required-term pair loss-internal-preference objective comparison

## 本版目标和边界

v623 把 v620-v622 的三条真实训练路线合并比较。它不训练新模型，而是把 fixed-only、loss-only、pair-full 等行为转成结构化报告，服务后续 route decision。

本版不复用 fixed-retention 或 loss-branch comparison，因为本轮 objective 的语义是 loss-internal-preference，需要独立字段避免误判。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_comparison.py
src/minigpt/model_capability_required_term_pair_loss_internal_preference_objective_comparison_artifacts.py
scripts/run_model_capability_required_term_pair_loss_internal_preference_objective_comparison.py
tests/test_model_capability_required_term_pair_loss_internal_preference_objective_comparison.py
```

## 核心数据结构

`source_reports` 记录每个输入 refresh report 的状态、corpus mode、seed 和训练产物存在性。

`term_rows` 从 replay report 中抽取 `fixed` / `loss` 的 continuation 命中情况。

`branch_rows` 汇总每条路线的：

- `hit_terms`
- `missed_terms`
- `fixed_only_tradeoff`
- `loss_only_tradeoff`
- `pair_full_observed`

## 运行结果

```text
decision=loss_internal_preference_objectives_confirm_branch_tradeoff
pair_full_report_count=0
fixed_only_tradeoff_report_count=2
loss_only_tradeoff_report_count=1
union_hit_terms=fixed,loss
```

这个结果很关键：它不是“全失败”，而是“两个分支分别能被学到，但不能共存”。

## 测试覆盖

新增测试覆盖：

- 三条路线 fixed-only/loss-only 混合时，decision 为 branch tradeoff。
- 非 loss-internal corpus mode 会失败，防止误接旧路线。
- JSON/CSV/text/Markdown/HTML 五种输出可生成。

## 一句话总结

v623 把 v620-v622 从零散训练结果收束成 branch tradeoff 证据，为 forced-choice 诊断提供输入。

# v608 required-term pair fixed-retention batch closeout

## 本版目标和边界

v608 给 v599-v607 的 fixed-retention 批次做收口。它不是继续增加语料变体，而是把已有证据转成机器可读结论：当前 fixed-retention / loss-rebalance 路线是否还能继续推进。

本版不训练新 checkpoint，不宣称模型能力提升，也不新增独立治理链；它是当前实验批次的结束判定。

## 前置链路

```text
v599: fixed-retention objective corpus modes
v600-v602: balanced / first-token / prompt-guard 三条真实 seed route
v603: objective comparison，确认 branch tradeoff
v604: route decision，选择 v601 作为 fixed recovery evidence
v605: loss-rebalance corpus modes
v606-v607: loss-rebalance / dual-cycle 两条真实 seed route
v608: batch closeout
```

这条链路的重点不是“某一步看起来有正向信号”，而是检查它能否稳定保住 `fixed=` 和 `loss=` 两个分支。

## 关键文件

```text
src/minigpt/model_capability_required_term_pair_fixed_retention_batch_closeout.py
src/minigpt/model_capability_required_term_pair_fixed_retention_batch_closeout_artifacts.py
scripts/run_model_capability_required_term_pair_fixed_retention_batch_closeout.py
tests/test_model_capability_required_term_pair_fixed_retention_batch_closeout.py
e/608/解释/model-capability-required-term-pair-fixed-retention-batch-closeout/
```

核心判定模块负责读取输入报告、分类 branch 行、统计 pair-full/fixed-only/loss-only，并输出 closeout decision。

artifact 模块负责渲染 JSON、CSV、text、Markdown、HTML，不把报告渲染逻辑塞回判定模块，避免继续制造大文件。

## 数据结构

`evidence_rows` 分三类：

```text
control: v603 comparison、v604 route decision
initial-objective: v600-v602 初始 fixed-retention 训练结果
loss-rebalance: v606-v607 loss-rebalance 训练结果
```

每条 refresh row 记录：

```text
label
phase
status
decision
corpus_mode
training_status
checkpoint_exists
pair_full_observed
hit_terms
missed_terms
branch_class
```

`branch_class` 是本版核心字段：

```text
pair-full
fixed-only
loss-only
partial
all-miss
```

它把长报告压缩成 closeout 能直接消费的判断。

## 运行结果

真实归档命令读取 v600、v601、v602、v603、v604、v606、v607，输出：

```text
status=pass
decision=close_fixed_retention_loss_rebalance_batch_before_new_design
loss_rebalance_pair_full_count=0
loss_rebalance_tradeoff_confirmed=True
stop_current_loss_rebalance_routes=True
model_quality_claim=negative_tradeoff_evidence
```

含义是：

- v606 恢复 loss 但丢 fixed。
- v607 恢复 fixed 但丢 loss。
- 当前 loss-rebalance 分支已经证明是 tradeoff，不是 pair-full candidate。

## 测试覆盖

新增测试覆盖：

- loss-rebalance 两条路线分别为 loss-only / fixed-only 时，closeout 决策为停止当前分支。
- 如果某条 loss-rebalance route 出现 pair-full，决策会转入 seed-stability，而不是误停。
- loss-rebalance 输入少于两条时，`--require-pass` 会失败。
- JSON/CSV/text/Markdown/HTML 五种输出都能生成。
- locator 能接受 output directory。

这些断言保护的是 closeout 的方向性：负结果收束，正结果进入稳定性验证，输入缺失不允许假装通过。

最终验证：

```text
python -m pytest tests\test_model_capability_required_term_pair_fixed_retention_batch_closeout.py tests\test_model_capability_required_term_pair_fixed_retention_objective_comparison.py tests\test_model_capability_required_term_pair_fixed_retention_route_decision.py tests\test_model_capability_required_term_pair_fixed_retention_loss_rebalance_corpus.py -q -o cache_dir=runs\pytest-cache-v608-targeted
17 passed

python -m pytest -q -o cache_dir=runs\pytest-cache-v608-full
1208 passed

python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local-v608
status=pass
clean_count=700
```

## 运行证据

```text
e/608/解释/model-capability-required-term-pair-fixed-retention-batch-closeout/
e/608/图片/v608-fixed-retention-batch-closeout.png
```

JSON 是后续模块可消费的源证据；HTML 和截图用于人工审查；`说明.md` 解释本版边界和结论。

## 一句话总结

v608 把 fixed-retention / loss-rebalance 批次从“继续试路线”收束为“停止当前分支，换 objective 设计”。

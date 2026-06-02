# v704 pair-readiness split plan

## 本版目标和边界

v704 的目标是把 v703 的 minimal prompt closeout 转成下一步 pair-readiness split plan。它解决的是“下一轮训练应该怎么设计输入和评估边界”，而不是继续新增同族 corpus mode。

本版不训练模型，不生成 checkpoint，不宣称模型能力提升。

## 前置链路

v703 的结论是：

```text
decision=minimal_prompt_batch_closed_without_pair_full
report_count=3
pair_full_report_count=0
fixed_only_report_count=1
loss_only_report_count=2
```

这说明 tiny 模型可以分别被推向 fixed 或 loss，但没有稳定学会 pair-full。因此 v704 的合理动作是先做 split plan。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_readiness_split_plan.py`
  - builder。
  - 读取 v703 closeout。
  - 检查 closeout 是否通过、是否无 pair-full、是否至少三份真实报告、是否存在 fixed-only 与 loss-only 混合失败。

- `src/minigpt/model_capability_required_term_pair_readiness_split_plan_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - 页面展示 checks、training split、evaluation split 和 promotion guard。

- `scripts/run_model_capability_required_term_pair_readiness_split_plan.py`
  - CLI。
  - 输入 closeout JSON 或目录。

- `tests/test_model_capability_required_term_pair_readiness_split_plan.py`
  - 覆盖 ready、pair-full 阻断、缺少 mixed failures 阻断、输出格式。

## Check 设计

v704 的 checks 包含：

```text
closeout_passed
closeout_decision
three_real_reports
no_pair_full
mixed_failures
```

其中 `mixed_failures` 很关键：如果只有一种失败形态，split plan 证据不足；只有 fixed-only 和 loss-only 都出现过，才说明两个分支都能单独赢，只是不能共存。

## Plan 内容

输出 plan：

```text
proposed_next_artifact=pair_readiness_split_contract
training_split=[
  direct_branch_completion_rows,
  anti_contamination_rows,
  balanced_prefix_progression_rows
]
evaluation_split=[
  fixed=,
  loss=,
  heldout_fixed_loss_pair_probe
]
```

promotion guard：

```text
claim pair capability only when heldout fixed and loss continuations both hit
```

这避免了“训练样本表面复读”被误判成能力提升。

## 运行证据

v704 输出：

```text
status=pass
decision=pair_readiness_split_plan_ready
plan_ready=True
model_quality_claim=plan_only
```

证据目录：

```text
e/704/解释/model-capability-required-term-pair-readiness-split-plan/
e/704/图片/v704-pair-readiness-split-plan.png
```

## 一句话总结

v704 把三次 minimal prompt 负结果转成训练/评估分离计划，避免继续用同一类 prompt 行盲目推进。

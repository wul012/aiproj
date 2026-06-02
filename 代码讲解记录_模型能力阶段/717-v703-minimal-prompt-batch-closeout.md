# v703 minimal prompt batch closeout

## 本版目标和边界

v703 的目标是关闭 v696-v702 的 minimal prompt 训练小批次。它读取三次真实训练报告，判断这条路线是否已经证明“继续同族修复收益不足”。

本版不训练模型，不新增 corpus mode，也不宣称模型能力提升。它是一个实验路线收口版本。

## 前置链路

v703 依赖三次真实训练：

```text
v696 -> minimal_prompt_equals_surface_objective -> fixed-only
v699 -> minimal_prompt_loss_first_token_repair_objective -> loss-only
v702 -> minimal_prompt_balanced_first_token_repair_objective -> loss-only
```

这三次训练都生成了 checkpoint，但都没有 `pair_full_observed=True`。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_batch_closeout.py`
  - closeout builder。
  - 读取多份 coexistence refresh 报告。
  - 提取 branch class、corpus mode、checkpoint 状态、pair-full 状态和生成样本。

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_batch_closeout_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
  - 把 evidence rows 做成可审阅表格。

- `scripts/run_model_capability_required_term_pair_minimal_prompt_batch_closeout.py`
  - CLI。
  - 支持多次传入 `--report label=path`。

- `tests/test_model_capability_required_term_pair_minimal_prompt_batch_closeout.py`
  - 覆盖 pass closeout、pair-full candidate 阻止 closeout、少于三份报告失败、输出格式。

## 核心数据结构

每个 evidence row 包含：

```text
label
path
status
decision
corpus_mode
training_status
checkpoint_exists
pair_full_observed
hit_terms
branch_class
fixed_generated
loss_generated
model_quality_claim
```

`branch_class` 是本版最重要的归类字段：

- `pair-full`：同时命中 fixed/loss。
- `fixed-only`：只命中 fixed。
- `loss-only`：只命中 loss。
- `all-miss`：两个都没命中。
- `partial-other`：非预期命中形态。

## 判定逻辑

closeout 通过需要：

- 至少三份真实训练报告。
- 每份报告 `status=pass`。
- 每份报告都存在 checkpoint。
- 没有任何 `pair-full` candidate。

如果存在 pair-full，v703 不允许 closeout，因为那说明路线可能应该进入 candidate promotion，而不是被关闭。

## 运行证据

v703 输出：

```text
status=pass
decision=minimal_prompt_batch_closed_without_pair_full
report_count=3
pair_full_report_count=0
fixed_only_report_count=1
loss_only_report_count=2
```

证据目录：

```text
e/703/解释/model-capability-required-term-pair-minimal-prompt-batch-closeout/
e/703/图片/v703-minimal-prompt-batch-closeout.png
```

## 这版为什么重要

v703 防止项目进入“每失败一次就再造一个类似 corpus mode”的循环。它把三次训练负结果合并成一个工程判断：当前瓶颈不是单个 prompt 行权重，而是 minimal prompt 条件下 tiny 模型没有稳定分离 fixed/loss 两个分支。

因此后续更合理的方向是：

- 训练前 pair-readiness split。
- 更明确的反污染检查。
- 更稳的训练/评估分离。

## 一句话总结

v703 用三次真实训练负样本正式关闭同族 minimal prompt 修复路线，把下一步导向更可诊断的 pair-readiness 能力建设。

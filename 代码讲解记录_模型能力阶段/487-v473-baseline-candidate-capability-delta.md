# v473：baseline-candidate capability delta

## 本版目标与边界

v473 的目标是回应“模型本身到底有没有变强”这个问题。前面很多版本完善了训练治理、receipt contract、CI gate 和证据链，但这些更多证明工程过程可复核，不等于模型能力提升。

本版把真实 tiny 训练产生的能力指标纳入 baseline-candidate eval loop：scorecard 分数、best/final validation loss、generation-quality flags。它不新增治理链，也不宣称 tiny GPT 已经具备生产级语言能力；它只把可观察指标摆出来，让后续模型能力讨论有数据基础。

## 关键修改文件

- `src/minigpt/tiny_scorecard_comparison_smoke_summary.py`
  - `smoke_summary()` 新增训练 loss 和 generation-quality flag 字段。
  - baseline/candidate 的 tiny smoke 不再只暴露 scorecard score，也带出真实训练过程指标。
- `src/minigpt/tiny_scorecard_comparison_smoke_outputs.py`
  - text 输出新增 baseline/candidate 的 best val loss、final val loss 和 generation flags。
  - CLI 输出可以直接看到能力指标，而不用打开 JSON。
- `src/minigpt/baseline_candidate_eval_loop.py`
  - baseline/candidate metrics 新增 loss 与 generation-quality 字段。
  - `delta_report` 新增 `training_best_val_loss_delta`、`training_final_val_loss_delta`、`generation_quality_total_flags_delta`。
  - Markdown/HTML/text 都展示这些 delta，并标明 loss 和 flags 是 lower is better。
- `tests/test_baseline_candidate_eval_loop.py`
  - fake summary fixture 增加训练 loss 和 generation flags。
  - 断言 delta 计算正确：best loss `-0.3`、final loss `-0.4`、flags `-2.0`。

## 核心数据结构

baseline/candidate metrics 现在包含：

```text
overall_score
training_best_val_loss
training_final_val_loss
generation_quality_status
generation_quality_total_flags
eval_suite_case_count
pair_same_checkpoint_baseline
```

delta report 现在包含：

```text
overall_score_delta
training_best_val_loss_delta
training_final_val_loss_delta
generation_quality_total_flags_delta
loss_delta_interpretation = negative_is_better
generation_flag_delta_interpretation = negative_is_better
```

这样报告能同时回答三件事：任务评分有没有变、训练 loss 有没有变、生成质量告警有没有变。

## 运行流程

```text
run_baseline_candidate_eval_loop.py
  -> run_tiny_scorecard_comparison_smoke.py
  -> baseline tiny train/eval/quality/scorecard
  -> candidate tiny train/eval/quality/scorecard
  -> scorecard comparison
  -> benchmark scorecard decision
  -> baseline_candidate_eval_loop report
```

v473 的真实运行使用同 seed，把主要变量集中到训练步数：

```text
baseline max_iters = 1
candidate max_iters = 4
seed = 1337
```

## 本次实验结果

本次 candidate 没有被接受：

```text
decision = reject_candidate
overall_score_delta = 0.0
best_val_loss_delta = -0.0031
generation_flags_delta = 0.0
```

这说明 candidate 的 best validation loss 有轻微改善，但 scorecard 和生成质量 flags 没有改善。换句话说，本版观察到的是“训练 loss 轻微下降”，不是“语言能力明显提升”。

## 测试覆盖

测试覆盖了两个重点：

- fake summary 中 loss/flags delta 计算准确，并出现在 text 输出中。
- 既有 baseline-candidate handoff/check 测试继续通过，说明新增能力指标没有破坏下游 handoff 结构。

目标测试：

```text
python -m pytest tests/test_baseline_candidate_eval_loop.py tests/test_baseline_candidate_handoff.py tests/test_baseline_candidate_handoff_check.py -q -o cache_dir=runs/pytest-cache-v473-focused
```

## 运行证据

证据目录：`e/473`

主要文件：

- `e/473/解释/baseline-candidate-eval-loop/baseline_candidate_eval_loop.json`
- `e/473/解释/baseline-candidate-eval-loop/baseline_candidate_eval_loop.html`
- `e/473/解释/baseline-candidate-eval-loop-cli.txt`
- `e/473/图片/01-baseline-candidate-capability-delta.png`

这些证据来自真实 CPU tiny training，不是手写 fixture；但它仍是教育级 tiny 实验，不能外推为生产模型质量。

## 一句话总结

v473 把 MiniGPT 的推进重点从“治理链可复核”转向“模型能力可观测”，并用真实 tiny 训练结果证明本次只有微弱 loss 改善，还不足以接受候选模型。

# v698 minimal prompt loss first-token repair plan

## 本版目标和边界

v698 的目标是把 v697 的诊断结论转成下一轮可执行训练计划。v697 已证明 `loss=` 在 seed `3535` 下会以 `fixed` 开头；v698 因此新增 `minimal_prompt_loss_first_token_repair_objective`，并生成 repair plan。

本版不训练 checkpoint，不判断模型能力提升。它是修复计划版。

## 前置链路

v697 的关键结论：

```text
decision=minimal_prompt_branch_bias_fixed_absorbs_loss
fixed_hit_count=2
loss_hit_count=0
loss_prompt_fixed_start_count=2
dominant_bias=fixed
```

v698 只在这个条件满足时生成 plan。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_objective_corpus.py`
  - 新增 `minimal_prompt_loss_first_token_repair_objective`。
  - 对 loss prefix 和 loss direct target 加权，同时保留 fixed direct rows。

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan.py`
  - builder。
  - 检查 v697 诊断是否真的证明 fixed absorbs loss。
  - 输出 proposed corpus mode、seed、repair focus 和下一步动作。

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan_artifacts.py`
  - 输出层。

- `scripts/run_model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan.py`
  - CLI。

- `tests/test_model_capability_required_term_pair_minimal_prompt_loss_first_token_repair_plan.py`
  - focused tests。

## 语料修复点

新 mode 加强：

- `loss=l`
- `loss=lo`
- `loss=los`
- `loss=loss`
- `loss first token after loss= is l`
- `loss branch does not start fixed`

同时保留：

- `fixed=f`
- `fixed=fi`
- `fixed=fix`
- `fixed=fixed`

设计意图是加强 loss 首 token，而不是删除 fixed 能力。

## Plan 检查项

`check_rows` 包括：

- `diagnostic_passed`
- `fixed_absorbs_loss_confirmed`
- `loss_hit_absent`
- `fixed_hit_present`
- `dominant_bias_fixed`

只有这些都成立，v698 才输出 `minimal_prompt_loss_first_token_repair_plan_ready`。

## 运行证据

正式证据：

```text
e/698/解释/model-capability-required-term-pair-minimal-prompt-loss-first-token-repair-plan/
e/698/图片/v698-minimal-prompt-loss-first-token-repair-plan.png
```

核心输出：

```text
proposed_corpus_mode=minimal_prompt_loss_first_token_repair_objective
seed_to_rerun=3535
repair_focus=loss_first_token_and_branch_separation
```

## 下一步

v699 应该真实 rerun seed `3535`：

```text
corpus_mode=minimal_prompt_loss_first_token_repair_objective
```

如果仍失败，再比较 v696/v699，判断是 loss 修复不足还是引入了 fixed 回退。

## 一句话总结

v698 把 fixed-dominant branch-bias 诊断转成 loss-first-token 修复语料和可执行训练计划。

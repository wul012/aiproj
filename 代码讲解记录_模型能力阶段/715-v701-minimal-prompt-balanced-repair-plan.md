# v701 minimal prompt balanced repair plan

## 本版目标和边界

v701 的目标是把 v700 的 first-token tradeoff 转成 balanced repair plan。它新增 `minimal_prompt_balanced_first_token_repair_objective`，但不训练 checkpoint。

本版只做计划和语料注册，不做模型能力 claim。

## 前置链路

v700 输出：

```text
decision=first_token_preference_tradeoff_confirmed
mixed_branch_tradeoff_confirmed=True
other_term_start_count=4
```

这说明 v696/v699 已形成 fixed-only 与 loss-only 的对称失败。v701 因此提出 balanced repair。

## 关键文件

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_objective_corpus.py`
  - 新增 `minimal_prompt_balanced_first_token_repair_objective`。

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_balanced_repair_plan.py`
  - builder。
  - 读取 v700 tradeoff report，确认 tradeoff 成立且没有 pair-full candidate。

- `src/minigpt/model_capability_required_term_pair_minimal_prompt_balanced_repair_plan_artifacts.py`
  - 输出层。

- `scripts/run_model_capability_required_term_pair_minimal_prompt_balanced_repair_plan.py`
  - CLI。

- `tests/test_model_capability_required_term_pair_minimal_prompt_balanced_repair_plan.py`
  - focused tests。

## 语料设计

balanced mode 对 fixed 和 loss 使用对称行：

```text
fixed=f
fixed=fi
fixed=fix
fixed=fixed
loss=l
loss=lo
loss=los
loss=loss
```

并加入明确约束：

```text
fixed branch does not start loss
loss branch does not start fixed
```

它不加入 `fixed=fixed|loss=loss` 这类 answer-bearing contextual anchor。

## Plan 检查

v701 要求：

- tradeoff report pass。
- decision 是 `first_token_preference_tradeoff_confirmed`。
- `mixed_branch_tradeoff_confirmed=True`。
- `pair_full_report_count=0`。

这样避免在已经有 pair-full candidate 时继续改 corpus。

## 运行证据

```text
e/701/解释/model-capability-required-term-pair-minimal-prompt-balanced-repair-plan/
e/701/图片/v701-minimal-prompt-balanced-repair-plan.png
```

核心输出：

```text
proposed_corpus_mode=minimal_prompt_balanced_first_token_repair_objective
seed_to_rerun=3535
repair_focus=balanced_first_token_and_direct_target_retention
```

## 下一步

v702 应按 plan 真实训练：

```text
corpus_mode=minimal_prompt_balanced_first_token_repair_objective
seed=3535
```

## 一句话总结

v701 把 fixed-only / loss-only tradeoff 收敛为对称 first-token repair plan。

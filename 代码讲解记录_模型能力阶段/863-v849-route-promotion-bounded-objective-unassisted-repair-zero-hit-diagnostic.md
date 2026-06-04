# v849：bounded objective unassisted repair zero-hit diagnostic

## 本版目标和边界

v849 的目标是解释 v848 的 zero-hit 失败，而不是继续训练。

边界：

- 不新增 checkpoint。
- 不修改 replay scoring。
- 不使用 decoder anchor。
- 不把 near-miss 当成命中。

这版回答：v847 的 unassisted repair checkpoint 为什么仍然没有生成完整 `fixed/loss`。

## 前置链路

输入来自三版：

- v846 seed/corpus：提供训练数据和 corpus text。
- v847 training run：提供 loss、checkpoint 和训练摘要。
- v848 replay comparison：提供真实 continuation 和 zero-hit 结果。

v849 检查：

```text
bounded_objective_unassisted_repair_replay_comparison_ready=True
objective_contract_recovered=False
zero_hit_case_count=3
bounded_objective_unassisted_repair_seed_ready=True
bounded_objective_unassisted_repair_training_ready=True
```

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic.py`
  - v849 adapter。复用 v840 diagnostic engine，把 v846/v847/v848 的 unassisted 字段映射到通用诊断输入。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic_artifacts.py`
  - 复用通用 zero-hit diagnostic renderer，并写入 v849 专属文件名。
- `scripts/diagnose_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit.py`
  - CLI 入口。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic.py`
  - 覆盖 near-miss zero-hit、training not ready、writer/CLI。
- `e/849/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-zero-hit-diagnostic/`
  - 保存真实诊断产物。
- `e/849/图片/v849-bounded-objective-unassisted-repair-zero-hit-diagnostic-html.png`
  - Playwright MCP 截图。

## 为什么复用 v840 engine

v840 已经实现了通用 zero-hit 诊断：

```text
replay rows -> prompt_in_corpus -> near_miss_terms -> root_causes -> next_step
```

v849 只是换了路线语义：输入不再是 v838 direct seed，而是 v846/v847/v848 的 unassisted repair branch。

因此 v849 adapter 做三件事：

1. 把 `bounded_objective_unassisted_repair_replay_comparison_ready` 映射到通用 replay ready。
2. 把 `bounded_objective_unassisted_repair_seed_ready` 映射到通用 seed ready。
3. 把 `bounded_objective_unassisted_repair_training_ready` 映射到通用 training ready。

这样避免重复维护 near-miss 和 root-cause 算法。

## 核心字段

v849 summary 包含：

```text
bounded_objective_unassisted_repair_zero_hit_diagnostic_ready
case_count
zero_hit_case_count
near_miss_case_count
prompt_in_corpus_count
root_cause_count
train_loss_delta
proposed_next_artifact
next_step
decoder_anchor_used
```

`decoder_anchor_used=False` 是本版的边界字段。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit_diagnostic_ready
case_count=3
zero_hit_case_count=3
near_miss_case_count=1
prompt_in_corpus_count=3
root_cause_count=4
model_quality_claim=not_improved_diagnosed
next_action=build_bounded_objective_unassisted_repair_curriculum_revision
```

case diagnostics：

```text
canonical_direct_completion -> zero_required_term_generation
minimal_direct_completion -> zero_required_term_generation
completion_label_surface -> near_miss_character_substitution_without_exact_term
```

root causes：

```text
objective_replay_zero_required_term_hits
near_miss_character_substitution
direct_prompts_present_but_generation_unanchored
loss_reduction_did_not_transfer_to_exact_generation
```

## 测试覆盖

focused pytest 覆盖：

- `los` 能被识别为 `loss` 的 near-miss，但不算 hit。
- unassisted training not ready 时诊断失败。
- artifact writer 和 CLI 输出完整。

focused pytest：

```text
3 passed
```

全量回归：

```text
1725 passed
```

source encoding hygiene：

```text
status=pass
source_count=1256
syntax_error_count=0
```

## 运行证据

真实命令：

```text
python scripts/diagnose_model_capability_route_promotion_bounded_objective_unassisted_repair_zero_hit.py --replay-comparison e/848/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-replay-comparison --unassisted-repair-seed e/846/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed --training-run e/847/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-training-run --corpus e/846/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_corpus.txt --out-dir e/849/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-zero-hit-diagnostic --require-diagnostic-ready --force
```

HTML 截图：

```text
e/849/图片/v849-bounded-objective-unassisted-repair-zero-hit-diagnostic-html.png
```

## 一句话总结

v849 证明 zero-hit 不是因为 prompt 不在数据里，而是训练后的生成仍不能稳定落到精确目标词；下一步应该修 curriculum。

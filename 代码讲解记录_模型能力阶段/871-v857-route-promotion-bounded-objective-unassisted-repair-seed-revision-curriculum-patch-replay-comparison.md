# v857：bounded objective unassisted repair seed revision curriculum patch replay comparison

## 本版目标和边界

v857 的目标是把 v856 checkpoint 放回 v836 bounded objective contract replay，判断 v855 curriculum patch 是否真正恢复 `fixed loss`。

边界：

- 不训练。
- 不使用 decoder anchor。
- 不修改 objective contract。
- 不把 partial hit 当作能力恢复。

这版是 v855/v856 的真实能力验收。

## 前置链路

```text
v854 partial-hit diagnostic
 -> v855 curriculum patch
 -> v856 patched-corpus training run
 -> v857 replay comparison
```

v856 只是 `training_artifact_only`，因此 v857 才能给能力结论。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison.py`
  - v857 adapter。把 v856 training-ready summary 映射到 v853 replay builder。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison_artifacts.py`
  - v857 专属 JSON/CSV/TXT/Markdown/HTML writer。
- `scripts/run_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison.py`
  - CLI 入口。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_comparison.py`
  - 覆盖 partial-hit、all-pass holdout、writer/CLI。
- `e/857/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-seed-revision-curriculum-patch-replay-comparison/`
  - 保存真实 replay 产物。
- `e/857/图片/v857-bounded-objective-unassisted-repair-seed-revision-curriculum-patch-replay-comparison-html.png`
  - Playwright MCP 截图。

## adapter 映射

v853 replay builder 期望：

```text
bounded_objective_unassisted_repair_seed_revision_training_ready
```

v856 输出：

```text
bounded_objective_unassisted_repair_seed_revision_curriculum_patch_training_ready
```

v857 adapter 只做字段映射，并把 route 改成：

```text
bounded_objective_unassisted_repair_seed_revision_curriculum_patch
```

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_replay_partial_required_term_hit
objective_contract_recovered=False
canonical_case_pass=False
case_count=3
passed_case_count=0
any_hit_case_count=2
zero_hit_case_count=1
pass_rate=0.0
promotion_ready=False
model_quality_claim=partial_required_term_signal
next_action=diagnose_bounded_objective_unassisted_repair_seed_revision_curriculum_patch_partial_hit_before_more_training
```

## replay 行为解释

三个 case：

```text
canonical_direct_completion -> " fixed l"   hit fixed, missed loss
minimal_direct_completion   -> " loswed "   missed fixed/loss
completion_label_surface    -> " fixed l"   hit fixed, missed loss
```

和 v853 对比：

- `completion_label_surface` 有进展，从 zero-hit 变成 fixed-only partial。
- `minimal_direct_completion` 退步，从 fixed-only partial 变成 zero-hit。
- `passed_case_count` 仍然是 0。

所以这不是 contract recovery，而是失败形态迁移。

## 测试覆盖

focused pytest 覆盖：

- partial-hit replay ready but not recovered。
- all-pass fake replay 会进入 holdout-required。
- CLI 和 writer 输出完整产物。

```text
3 passed
```

全量验证：

```text
py_compile: pass
full pytest: 1750 passed
source encoding: source_count=1288 clean_count=1288 bom_count=0 syntax_error_count=0
git diff --check: pass
```

## 运行证据

HTML 截图：

```text
e/857/图片/v857-bounded-objective-unassisted-repair-seed-revision-curriculum-patch-replay-comparison-html.png
```

Playwright MCP snapshot 确认页面展示：

```text
Status=pass
Recovered=False
Passed=0
Any hits=2
Zero hits=1
Claim=partial_required_term_signal
```

## 一句话总结

v857 证明 curriculum patch 改善了 completion surface，但还没有让模型通过 bounded objective contract。

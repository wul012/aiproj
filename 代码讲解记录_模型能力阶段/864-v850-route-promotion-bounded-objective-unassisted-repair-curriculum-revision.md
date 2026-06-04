# v850：bounded objective unassisted repair curriculum revision

## 本版目标和边界

v850 的目标是把 v849 的 zero-hit 诊断转成下一轮可执行课程修订。

边界：

- 不生成新 seed。
- 不训练 checkpoint。
- 不使用 decoder anchor。
- 不宣称模型能力提升。

这版只定义下一轮数据应该怎么修。

## 前置链路

输入来自 v849：

```text
e/849/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-zero-hit-diagnostic/
```

v849 已经证明：

```text
zero_hit_case_count=3
near_miss_case_count=1
prompt_in_corpus_count=3
root_cause_count=4
```

因此 v850 不再把失败归因于 prompt 缺失，而是围绕输出位置、精确 completion、碎片修正和 holdout 保留来设计 curriculum。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision.py`
  - 读取 v849 diagnostic，生成 revision items、acceptance gates、checks、summary 和 interpretation。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision.py`
  - CLI 入口。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision.py`
  - 覆盖正常 revision、diagnostic route 错误、writer/CLI。
- `e/850/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-curriculum-revision/`
  - 保存真实 curriculum revision。
- `e/850/图片/v850-bounded-objective-unassisted-repair-curriculum-revision-html.png`
  - Playwright MCP 截图。

## Curriculum Items

v850 生成 7 个 revision item：

```text
output_position_anchor_examples
neutral_prompt_exact_completion_repetition
fragment_contrast_examples
short_decoding_profile_probe
unchanged_contract_holdout
prompt_surface_balance
near_miss_fragment_tracking
```

所有 item 都有：

```text
decoder_anchor_allowed=False
promotion_claim_allowed=False
```

这保证下一轮仍然是 unassisted repair route。

## Acceptance Gates

v850 定义 4 个 gate：

```text
seed_revision_ready
training_artifacts_ready
unassisted_replay_improves
unchanged_contract_preserved
```

其中 `unassisted_replay_improves` 要求下一轮 replay 至少改善 `any_hit_case_count` 或 `pass_rate`，否则不能继续 promotion review。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision_ready
revision_item_count=7
acceptance_gate_count=4
decoder_anchor_allowed=False
promotion_claim_allowed=False
model_quality_claim=curriculum_revision_only
next_action=build_bounded_objective_unassisted_repair_seed_revision
```

## 测试覆盖

focused pytest 覆盖：

- v849 diagnostic 可生成 ready revision。
- diagnostic 没有指向 curriculum revision 时失败。
- artifact writer 和 CLI 输出完整。

focused pytest：

```text
3 passed
```

全量回归：

```text
1728 passed
```

source encoding hygiene：

```text
status=pass
source_count=1260
syntax_error_count=0
```

## 运行证据

真实命令：

```text
python scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_curriculum_revision.py --zero-hit-diagnostic e/849/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-zero-hit-diagnostic --out-dir e/850/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-curriculum-revision --require-revision-ready --force
```

HTML 截图：

```text
e/850/图片/v850-bounded-objective-unassisted-repair-curriculum-revision-html.png
```

## 一句话总结

v850 把失败诊断变成无锚点课程修订合同，为下一版 seed revision 提供清晰边界和验收门。

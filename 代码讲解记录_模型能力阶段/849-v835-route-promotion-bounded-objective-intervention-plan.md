# v835：bounded objective intervention plan

## 本版目标和边界

v835 的目标是把 v834 的路线判断转成一个可复核、可执行的 objective-contract intervention plan。v834 已经确认 rebalanced decoder-rescue 分支没有从 profile sweep 中恢复能力信号，因此 v835 不继续扩大采样、不继续直接训练，也不把治理产物包装成模型质量提升。

这一版只回答一个问题：下一步如果要重新做训练目标，必须先遵守什么目标契约、做哪些工件、过哪些闸门。

## 前置链路

本版输入来自 v834：

- `status=pass`
- `selected_intervention_track=objective_contract_intervention_first`
- `recommended_next_artifact=model_capability_route_promotion_bounded_objective_intervention_plan`
- `promotion_allowed=False`
- `new_training_allowed=False`
- `closed_route=decoder_anchor_rebalanced_rescue`

这些字段保证 v835 不是凭空开新链，而是接住 v829-v833 失败证据之后的保守路线。

## 关键文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_intervention_plan.py`
  - 负责读取 v834 decision，校验路线是否允许进入 objective contract intervention，并生成计划 JSON。
- `src/minigpt/model_capability_route_promotion_bounded_objective_intervention_plan_artifacts.py`
  - 负责把计划渲染成 JSON、CSV、TXT、Markdown 和 HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_intervention_plan.py`
  - 提供命令行入口，支持输入文件或目录、`--require-plan-ready` 和 `--force`。
- `tests/test_model_capability_route_promotion_bounded_objective_intervention_plan.py`
  - 覆盖正常计划、错误路线、训练未阻断、输出和 CLI 接线。
- `e/835/解释/model-capability-route-promotion-bounded-objective-intervention-plan/`
  - 保存真实运行的报告产物。
- `e/835/图片/v835-bounded-objective-intervention-plan-html.png`
  - 保存 Playwright MCP 截取的 HTML 运行截图。

## 核心数据结构

`objective_contract` 是本版最重要的结构：

```text
contract_id=bounded_fixed_loss_direct_completion_contract
target_terms=fixed, loss
canonical_prompt=Answer with exactly two tokens: fixed loss\nanswer:
canonical_completion=fixed loss
unchanged_suite_check_required=True
```

它有两个作用：

1. 把下一阶段的训练目标缩小到一个直接、可测的 canonical completion。
2. 保留 v803 bounded suite 作为 holdout，不允许只靠新契约过关就宣称旧路线恢复。

`work_items` 给出 5 个下一步工件：

- `contract_fixture`
- `direct_seed_corpus`
- `controlled_training`
- `dual_replay`
- `fallback_decision`

其中 `dual_replay` 很关键，因为它要求同时检查 canonical contract 和未改动的 v803 suite；这能防止模型只学会一个新提示，却仍不能证明 route promotion。

`acceptance_gates` 有 4 个：

- contract 必须保持 bounded。
- canonical replay 必须先过。
- v803 replay 仍必须保留。
- 如果 canonical replay 仍为 zero-hit，要转向 architecture capacity probe，而不是继续 patch seed。

## 运行流程

CLI 先用 `locate_intervention_decision()` 支持目录输入，例如传入 `e/834/解释/...` 时会自动定位 `model_capability_route_promotion_bounded_rebalanced_intervention_decision.json`。

随后 builder 做 6 个校验：

- source decision 必须是 pass。
- 必须选中 `objective_contract_intervention_first`。
- next artifact 必须指向本计划。
- promotion 必须仍被阻断。
- new training 必须仍被阻断。
- closed route 必须存在。

全部通过后，报告状态为 `pass`，输出 `decision=model_capability_route_promotion_bounded_objective_intervention_plan_ready`。

## 测试覆盖

聚焦测试 `tests/test_model_capability_route_promotion_bounded_objective_intervention_plan.py` 覆盖了四类风险：

- 正常 v834 decision 能生成 ready plan，并要求 `work_item_count=5`。
- 如果路线不是 `objective_contract_intervention_first`，计划失败。
- 如果 `new_training_allowed=True`，计划失败，防止还没定义目标契约就继续训练。
- artifact writer 和 CLI 都能输出 JSON、CSV、TXT、Markdown、HTML。

本版聚焦测试结果是 `4 passed`。

## 运行证据

真实命令使用 v834 产物生成 v835 报告：

```text
python scripts/build_model_capability_route_promotion_bounded_objective_intervention_plan.py --intervention-decision e/834/解释/model-capability-route-promotion-bounded-rebalanced-intervention-decision --out-dir e/835/解释/model-capability-route-promotion-bounded-objective-intervention-plan --require-plan-ready --force
```

关键输出：

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_intervention_plan_ready
proposed_next_artifact=model_capability_route_promotion_bounded_objective_contract
model_quality_claim=plan_only
```

Playwright MCP 截图保存到 `e/835/图片/v835-bounded-objective-intervention-plan-html.png`，用于证明 HTML 报告可浏览、非空，并展示了 Objective Contract 与 Work Items。

## 一句话总结

v835 把失败后的路线选择收束成了有边界的 objective contract intervention plan，让下一步训练必须先经过契约定义，而不是继续靠采样、seed patch 或训练轮次漂移。

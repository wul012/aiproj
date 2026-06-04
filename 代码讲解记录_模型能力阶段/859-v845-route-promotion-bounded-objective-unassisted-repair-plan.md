# v845：bounded objective unassisted repair plan

## 本版目标和边界

v845 的目标是把 v844 的结论转为下一阶段行动计划。v844 已经关闭 decoder anchor 作为能力路线；v845 因此不再继续沿 assisted anchor 方向推进，而是规划无锚点 objective repair。

边界：

- 不训练。
- 不新增 seed corpus。
- 不宣称模型质量提升。
- 不允许 route promotion。

这版是计划，不是能力证据。

## 前置链路

输入来自：

```text
e/844/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy-review/
```

v844 的关键字段是：

```text
assisted_anchor_path_closed=True
selected_track=unassisted_objective_repair
```

v845 要求这两个条件同时成立，否则 plan 会失败。

## 关键新增文件

- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_plan.py`
  - 构建 repair work items、acceptance gates、blocked actions、summary 和 interpretation。
- `src/minigpt/model_capability_route_promotion_bounded_objective_unassisted_repair_plan_artifacts.py`
  - 输出 JSON、CSV、TXT、Markdown、HTML。
- `scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_plan.py`
  - CLI 入口，支持 `--require-plan-ready`。
- `tests/test_model_capability_route_promotion_bounded_objective_unassisted_repair_plan.py`
  - 覆盖 plan ready、anchor path 未关闭时失败、输出和 CLI。
- `e/845/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-plan/`
  - 保存真实 plan 产物。
- `e/845/图片/v845-bounded-objective-unassisted-repair-plan-html.png`
  - Playwright MCP 截图。

## Work Items

v845 生成 5 个工作项：

- `unassisted_seed_revision`
- `first_token_targeting`
- `loss_token_targeting`
- `unassisted_training_run`
- `unchanged_holdout_replay`

这些工作项把问题拆成两段：

- 先解决无锚点生成 `fixed` 的 first-token uptake。
- 再解决模型自己生成 `fixed` 后继续生成 `loss` 的 second-token uptake。

## Acceptance Gates

v845 的 gate 是：

- `no_decoder_anchor_inference`
- `new_text_required_term_hit`
- `objective_contract_replay`
- `holdout_before_promotion`

这里最重要的是 `new_text_required_term_hit`。v843 的失败点正是 `new_text_pass_count=0`，所以后续不能再用 combined anchor hit 替代 continuation hit。

## Blocked Actions

v845 同时阻止三件事：

- 不把 anchor policy 晋级。
- 不继续训练 anchor 变体。
- 不用 loss 下降单独宣称质量提升。

这些 blocked actions 是为了防止项目再次绕回 assisted branch。

## 真实结果

```text
status=pass
decision=model_capability_route_promotion_bounded_objective_unassisted_repair_plan_ready
bounded_objective_unassisted_repair_plan_ready=True
route=bounded_objective_unassisted_repair
work_item_count=5
acceptance_gate_count=4
promotion_ready=False
model_quality_claim=plan_only
next_action=build_bounded_objective_unassisted_repair_seed
```

## 测试覆盖

测试覆盖：

- v844 关闭 anchor path 后 plan ready。
- anchor path 未关闭时失败。
- artifact writer 和 CLI 输出完整。

focused pytest：

```text
3 passed
```

## 运行证据

真实命令：

```text
python scripts/build_model_capability_route_promotion_bounded_objective_unassisted_repair_plan.py --policy-review e/844/解释/model-capability-route-promotion-bounded-objective-decoder-anchor-policy-review --out-dir e/845/解释/model-capability-route-promotion-bounded-objective-unassisted-repair-plan --require-plan-ready --force
```

HTML 截图：

```text
e/845/图片/v845-bounded-objective-unassisted-repair-plan-html.png
```

## 一句话总结

v845 把 v841-v844 的 assisted decoder anchor 分支转化为无锚点 repair 计划，后续能力推进必须以 continuation 自身命中 required terms 为验收标准。

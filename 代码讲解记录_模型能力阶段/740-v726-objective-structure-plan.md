# v726 objective-structure plan

## 本版目标和边界

v726 的目标是从 v725 five-route comparison 中推导下一步 objective-structure contract。

本版不训练、不修改 corpus、不改变模型规模。它是一个计划型证据版本：只有当 v725 证明 capacity-probe 相比 fixed-recovery 没有改善，并且 `loss` 仍然是 miss term 时，才允许进入 objective-structure 设计。

## 前置链路

```text
v722 four-route comparison
 -> row patching closeout
v723 capacity-probe plan
 -> controlled larger-tiny-model config
v724 capacity-probe training
 -> still fixed-only
v725 five-route comparison
 -> capacity_probe_no_improvement=True
v726 objective-structure plan
 -> build pair_readiness_objective_structure_contract
```

## 关键新增文件

- `src/minigpt/model_capability_required_term_pair_readiness_objective_structure_plan.py`
  - 读取 v725 route comparison。
  - 执行输入检查。
  - 输出 plan、summary、interpretation。
- `src/minigpt/model_capability_required_term_pair_readiness_objective_structure_plan_artifacts.py`
  - 负责 JSON/CSV/TXT/Markdown/HTML 五格式输出。
  - 保持主逻辑模块不混入渲染细节。
- `scripts/run_model_capability_required_term_pair_readiness_objective_structure_plan.py`
  - 提供 CLI 入口。
  - 支持输入 JSON 或输出目录。
- `tests/test_model_capability_required_term_pair_readiness_objective_structure_plan.py`
  - 覆盖 ready、失败输入、loss miss 检查和五格式渲染。

## 核心检查

v726 的 check rows 包含：

```text
route_comparison_passed
route_comparison_decision
no_pair_full_route
five_routes_present
capacity_probe_no_improvement
capacity_probe_no_delta
capacity_probe_still_misses_loss
capacity_probe_row_present
```

其中最关键的是：

```text
route_comparison_decision == pair_readiness_capacity_probe_no_improvement_fixed_only
capacity_probe_no_improvement == True
capacity_probe_vs_fixed_recovery_default_hit_delta == 0
capacity_probe_default_missed_terms contains loss
```

这些约束防止项目在尚未真正关闭 capacity-probe 路线时过早切换训练目标。

## Plan 语义

v726 输出的 proposed next artifact 是：

```text
pair_readiness_objective_structure_contract
```

objective strategy 包含四类要求：

- 在 answer token 前显式分离 fixed/loss task id。
- 增加一条样本内同时询问两条 branch 的 paired block rows。
- 保持 `fixed=`、`loss=` direct probes 为 heldout。
- 在 objective contract materialized and replayed 前，不继续扩大模型。

contract requirements 则约束后续 v727：

- 不能包含 exact heldout probes。
- fixed/loss row family 必须数量和模板角色均衡。
- paired rows 必须有正序和反序。
- 输出必须暴露 row family counts 和 leakage checks。

## 运行证据

运行证据目录：

- `e/726/解释/model-capability-required-term-pair-readiness-objective-structure-plan/`
- `e/726/图片/v726-objective-structure-plan.png`

这些产物是只读计划证据，后续 contract builder 可以消费 JSON 里的 `plan` 与 `source_route_comparison`。

## 测试覆盖

测试保护三类风险：

- 正常 v725 形态可以得到 `pair_readiness_objective_structure_plan_ready`。
- 如果 comparison decision 还停在旧 closeout，`--require-pass` 会失败。
- 如果 capacity probe 不再 miss `loss`，不能生成 objective-structure plan。
- 五格式 artifact 渲染包含关键 decision 和 HTML 标题。

## 一句话总结

v726 把“容量探针无收益”的负结果转成受检查的 objective-structure contract 计划，让下一版改训练目标有清晰边界。

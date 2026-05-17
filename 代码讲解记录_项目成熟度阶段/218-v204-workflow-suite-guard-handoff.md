# v204 workflow suite guard handoff 代码讲解

## 本版目标

v204 的目标是把 v203 新增的 strict suite-consistency decision guard 接入 consolidated training-scale workflow。

v203 已经让两个单点决策入口具备严格门禁：

- `decide_training_scale_run.py --require-suite-consistency`
- `decide_promoted_training_scale_baseline.py --require-suite-consistency`

但 `run_training_scale_workflow.py` 是一键入口，它内部会自动完成 plan -> gated runs -> comparison -> decision。如果 workflow 没有同等参数，那么用户通过一键 workflow 跑实验时仍然可能绕过 strict guard。

本版解决这个断点：workflow builder、workflow CLI、workflow JSON/CSV/Markdown/HTML 和 workflow tests 都显式携带 `decision_require_suite_consistency`。

## 不做什么

本版不改变 suite consistency 的计算逻辑，不改变 training scale run decision 的候选排序，不改变默认 workflow 行为，不训练模型，也不让 strict guard 成为默认开启。

默认不开启是有意的：workflow 仍可用于治理 triage 和历史证据复盘；只有需要干净模型质量比较时，才显式加 strict guard。

## `src/minigpt/training_scale_workflow.py`

`run_training_scale_workflow()` 新增参数：

```python
decision_require_suite_consistency: bool = False
```

它的位置靠近已有 decision 参数：

```python
decision_min_readiness
decision_require_gate_pass
decision_require_batch_started
decision_require_suite_consistency
decision_execute_out_root
```

这样语义清楚：它不是 plan/gate/run 参数，而是 workflow 内部 decision 层的资格条件。

## 传给内部 decision

workflow 在生成 comparison 后，会调用：

```python
decision = build_training_scale_run_decision(
    comparison_outputs["json"],
    min_readiness=decision_min_readiness,
    require_gate_pass=decision_require_gate_pass,
    require_batch_started=decision_require_batch_started,
    require_suite_consistency=decision_require_suite_consistency,
    ...
)
```

这意味着 strict guard 的实际阻断仍然只发生在 `training_scale_run_decision.py`。workflow 只是把策略参数传进去，不复制 decision 的判断逻辑。

这个边界很重要：

- comparison 负责计算 suite consistency。
- decision 负责按 strict guard 阻断候选。
- workflow 负责编排链路并保存结果。

## Workflow Report 字段

report 顶层新增：

```json
"decision_require_suite_consistency": true,
"require_suite_consistency": true
```

`decision_require_suite_consistency` 是准确字段名，说明它属于 workflow 内部 decision。`require_suite_consistency` 是便于人和工具快速读取的兼容别名，和 nested decision artifact 中的字段同名。

workflow summary 新增：

```json
{
  "selected_suite_path": "builtin:standard-zh",
  "decision_require_suite_consistency": true,
  "suite_consistency": "consistent",
  "suite_mismatch_count": 0
}
```

这些字段来自 nested decision summary。workflow 不重新推断 suite consistency，只把内部 decision 结果提升到 workflow summary，方便一键入口的审阅面直接显示。

## Workflow Recommendations

当：

```text
decision_require_suite_consistency=true
suite_consistency!=consistent
```

workflow recommendations 会增加：

```text
Fix workflow benchmark suite consistency before using the decision as clean model-quality evidence.
```

它是 workflow 层的解释，和 decision 层的 rejection reason 互补：

- decision 层解释为什么候选被拒绝。
- workflow 层解释为什么整个一键链路不应继续作为 clean model-quality evidence。

## `src/minigpt/training_scale_workflow_artifacts.py`

artifact 层新增三类展示：

CSV：

```text
decision_require_suite_consistency
suite_consistency
```

Markdown：

```text
Suite consistency
Require suite consistency
```

HTML stats：

```text
Suite consistency
Require suite consistency
```

这些 artifact 是只读证据。真正的 strict 行为仍在 nested decision JSON 中可查。

## `scripts/run_training_scale_workflow.py`

CLI 新增：

```text
--decision-require-suite-consistency
```

名称里保留 `decision-` 前缀，是为了和已有参数保持一致：

```text
--decision-min-readiness
--decision-require-gate-pass
--decision-no-require-batch-started
```

这样用户能看出它不是计划阶段或 gate 阶段参数，而是最终 decision 阶段参数。

## 测试覆盖

`tests/test_training_scale_workflow.py` 新增：

```python
test_workflow_passes_suite_consistency_guard_to_decision
```

测试断言：

- workflow report 顶层 `decision_require_suite_consistency` 为 `True`。
- workflow summary `decision_require_suite_consistency` 为 `True`。
- nested decision summary `require_suite_consistency` 为 `True`。
- nested decision JSON 中 `require_suite_consistency` 为 `True`。
- 当前同一 workflow plan 下 suite consistency 为 `consistent`，因此不会被 strict guard 误挡。

这个测试不是为了制造 mixed suite，而是为了保护“workflow 参数确实传到了 nested decision artifact”。

## 运行流程

普通 workflow：

```text
run_training_scale_workflow(..., decision_require_suite_consistency=False)
 -> build plan
 -> run profiles
 -> compare runs
 -> decision reads suite consistency but does not block mixed/missing by strict rule
 -> workflow summary records require_suite_consistency=false
```

strict workflow：

```text
run_training_scale_workflow(..., decision_require_suite_consistency=True)
 -> build plan
 -> run profiles
 -> compare runs
 -> decision blocks mixed/missing suite candidates
 -> workflow summary records require_suite_consistency=true
```

在标准 workflow 中，同一个 plan 生成的多个 profile 通常天然同 suite，所以 strict guard 不应误挡。它的价值主要在后续更复杂 workflow 或外部 comparison 输入扩展时，保证 workflow 层不会绕过 decision 层的 clean-comparison 策略。

## 证据边界

本版证明的是 strict guard 能进入 consolidated workflow，并能在 workflow artifact 中被审阅。

它不证明模型质量提升，也不新增任何评测题。它让训练规模治理链路更一致：单点 decision 和一键 workflow 使用同一套 suite-consistency 策略。

## 一句话总结

v204 把 suite-consistency strict guard 从单独 decision 入口推进到一键 training-scale workflow，让 workflow 也能按需执行 clean-comparison 门禁。

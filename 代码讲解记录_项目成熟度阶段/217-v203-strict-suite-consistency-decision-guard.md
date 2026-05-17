# v203 strict suite consistency decision guard 代码讲解

## 本版目标

v203 的目标是把 v202 新增的 suite-consistency evidence 变成可选的严格决策护栏。

v202 解决的是“看得见”：comparison 和 decision 报告会显示 `suite_consistency=mixed`，并提醒 mixed-suite delta 不能当作干净模型质量提升。v203 解决的是“挡得住”：当用户明确要求干净模型质量比较时，decision 可以因为 mixed/missing suite 直接 blocked。

## 不做什么

本版不改变默认行为，不训练模型，不改变 readiness 排序，不改变 comparison 的 suite 判断，也不禁止 mixed-suite 报告存在。

默认模式继续保留治理 triage 能力：mixed suite 可以帮助判断 gate、batch、promotion 和 execute handoff 是否完整。只有显式启用 `require_suite_consistency` / `--require-suite-consistency` 时，它才变成阻断条件。

## `src/minigpt/training_scale_run_decision.py`

`build_training_scale_run_decision()` 新增参数：

```python
require_suite_consistency: bool = False
```

这保持默认兼容。旧调用不传参数时，v202 的 mixed-suite recommendation 仍然存在，但不会改变候选选择。

新增 helper：

```python
def _suite_consistency_reasons(comparison_summary, require_suite_consistency) -> list[str]:
    if not require_suite_consistency:
        return []
    suite_consistency = str(comparison_summary.get("suite_consistency") or "")
    if suite_consistency == "consistent":
        return []
    return [f"benchmark suite consistency is {suite_consistency or 'missing'}"]
```

它的语义很窄：

- strict guard 未启用：不产生 rejection reason。
- suite 是 `consistent`：不产生 rejection reason。
- suite 是 `mixed` / `missing` / 空值：产生阻断原因。

候选循环中会把这个 reason 追加到每个 run 的 rejection reasons：

```python
reasons.extend(suite_reasons)
```

这样 strict guard 不需要重写 candidate selection 算法。它只是像 gate/readiness/batch 一样，成为一个额外的候选资格条件。

## Decision Summary

`_decision_summary()` 新增：

```json
"require_suite_consistency": true
```

这和已有字段放在同一层：

```json
{
  "selected_suite_path": "builtin:standard-zh",
  "require_suite_consistency": true,
  "suite_consistency": "mixed",
  "suite_paths": ["builtin:standard-zh", "data/eval_prompts.json"],
  "suite_mismatch_count": 1
}
```

这个设计让审阅者能同时看到：

- 当前 comparison 的事实状态：`suite_consistency`。
- 当前 decision 是否要求严格阻断：`require_suite_consistency`。
- 如果没有 selected run，为什么被拒绝：`rejected_runs[].reasons`。

## Recommendations

strict guard 启用且 suite 不 consistent 时，recommendations 会新增：

```text
Fix benchmark suite consistency before selecting an executable run for clean model-quality comparison.
```

这条建议和 v202 的 mixed-suite triage 提醒不是重复关系：

- v202 提醒解释边界。
- v203 strict guard 提醒阻断后的修复方向。

## `src/minigpt/training_scale_run_decision_artifacts.py`

artifact 层把 `require_suite_consistency` 写入：

- CSV 字段。
- Markdown 摘要。
- HTML stats 卡片。

这些是只读证据。真正的阻断逻辑只在 decision builder 里。

## `src/minigpt/promoted_training_scale_decision.py`

promoted baseline decision 同样新增：

```python
require_suite_consistency: bool = False
```

它读取 promoted comparison summary 里的 `suite_consistency`，并复用同样的 helper 语义。

默认模式下，如果 mixed suite 但候选满足 promoted baseline 条件，仍可 accepted，同时 recommendations 写出：

```text
Promoted runs use different benchmark suites; treat this baseline as governance triage, not clean model-quality evidence.
```

strict mode 下，候选会被加入 rejection reasons：

```text
benchmark suite consistency is mixed
```

于是 selected baseline 为空，decision status 变成 `blocked`。

## CLI 入口

`scripts/decide_training_scale_run.py` 新增：

```text
--require-suite-consistency
```

`scripts/decide_promoted_training_scale_baseline.py` 同样新增：

```text
--require-suite-consistency
```

这两个 CLI 都把参数直接传给 builder，不在脚本层重复判断。脚本仍然负责参数解析、写 artifact 和根据 blocked/require-accepted 规则设置退出码。

## 测试覆盖

`tests/test_training_scale_run_decision.py`

- `test_mixed_suite_summary_is_carried_into_decision_recommendations`
  - 验证默认 mixed suite 仍不阻断。
  - summary 中 `require_suite_consistency` 为 `False`。
- `test_require_suite_consistency_blocks_mixed_suite_decision`
  - 启用 strict guard。
  - decision status 变为 `blocked`。
  - `selected_run` 为 `None`。
  - rejected reasons 包含 `benchmark suite consistency is mixed`。

`tests/test_promoted_training_scale_decision.py`

- `test_require_suite_consistency_blocks_mixed_promoted_decision`
  - 默认 promoted mixed suite 仍可 accepted。
  - strict mode 下变为 blocked。
  - recommendations 明确提示修复 suite consistency。

## 运行流程

普通 training-scale decision：

```text
training_scale_run_comparison.json
 -> build_training_scale_run_decision(require_suite_consistency=False)
    -> mixed suite: review/ready can still be selected, with warning

training_scale_run_comparison.json
 -> build_training_scale_run_decision(require_suite_consistency=True)
    -> mixed/missing suite: all candidates rejected, decision_status=blocked
```

promoted baseline decision：

```text
promoted_training_scale_comparison.json
 -> build_promoted_training_scale_decision(require_suite_consistency=False)
    -> mixed suite: accepted/review can still exist, with triage warning

promoted_training_scale_comparison.json
 -> build_promoted_training_scale_decision(require_suite_consistency=True)
    -> mixed/missing suite: selected_baseline=None, decision_status=blocked
```

## 证据边界

本版让项目更严格，但没有把严格模式设为默认。原因是 aiproj 仍然是学习型 AI 工程治理项目，很多时候需要保留不完整或 mixed 的证据来解释为什么不能发布、不能 promote，或者为什么只能做人工 review。

严格模式适合以下场景：

- 要把 promoted baseline 作为下一轮模型质量比较依据。
- 要在同一套 benchmark suite 下比较 readiness/score 的变化。
- 要避免 mixed-suite run 被误读成模型能力提升。

默认模式适合以下场景：

- 做执行链路排查。
- 做 gate/batch/promotion 完整性 review。
- 回看历史 mixed-suite 证据。

## 一句话总结

v203 把 suite-consistency 从“报告里的解释字段”升级成“按需启用的决策门禁”，同时保留默认治理兼容性。

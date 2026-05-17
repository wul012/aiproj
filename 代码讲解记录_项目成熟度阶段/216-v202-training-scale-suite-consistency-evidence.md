# v202 training scale suite consistency evidence 代码讲解

## 本版目标

v202 的目标是把 benchmark suite 选择从“能被训练规模链路携带”推进到“能在比较和决策时被审计”。

v198 新增标准中文 `standard-zh` suite，v199-v201 让它进入 training portfolio、batch、scale workflow、promoted seed 和 seed handoff。现在的风险不在传递，而在解释：如果两个 runs 用了不同 suite，readiness delta、gate delta 和 promoted baseline 选择仍然可以用于执行治理，但不能被当成干净的模型质量对比。

本版解决这个解释断点：training scale run comparison、training scale run decision、promoted comparison、promoted baseline decision 都会输出 suite 一致性字段，并在 mixed suite 时给出边界提示。

## 不做什么

本版不新增评测题，不训练模型，不改变 gate/profile/readiness 规则，不改变 baseline 选择算法，也不禁止 mixed suite 比较。

mixed suite 仍然可以比较，因为它对治理有价值：比如确认哪个 run 完成了 batch、哪个 gate 被挡住、哪个候选可执行。但它必须被标记为“不是干净模型质量 delta”。

## 关键文件

### `src/minigpt/training_scale_run_comparison.py`

`_run_summary()` 现在从 run report 中读取 suite 字段：

```python
"suite_mode": plan.get("suite_mode") or batch.get("suite_mode"),
"suite_name": plan.get("suite_name") or batch.get("suite_name"),
"suite_path": plan.get("suite_path") or batch.get("suite_path"),
```

这里优先读取 `scale_plan_summary`，再回退到 `batch_summary`。这样旧链路和新链路都能被兼容读取。

`_comparison_summary()` 新增四类 suite 证据：

```json
{
  "baseline_suite_path": "builtin:standard-zh",
  "suite_consistency": "consistent",
  "suite_paths": ["builtin:standard-zh"],
  "suite_mismatch_count": 0
}
```

字段含义：

- `baseline_suite_path`：baseline run 使用的 suite。
- `suite_consistency`：`consistent`、`mixed` 或 `missing`。
- `suite_paths`：本次比较中实际出现过的 suite path 集合。
- `suite_mismatch_count`：相对 baseline 发生 suite 变化的 delta 数量。

新增 `_suite_relation()`：

```text
unchanged  -> run 与 baseline suite 相同
changed    -> 两边都有 suite_path，但值不同
unknown    -> 任一侧缺失 suite_path
```

`_delta_explanation()` 也会在 suite 不同时追加：

```text
suite data/eval_prompts.json -> builtin:standard-zh
```

这让 CSV、Markdown、HTML 不只是显示一个 mixed 总结，也能指出哪一个 run 相对 baseline 换了评测基准。

## `src/minigpt/training_scale_run_decision.py`

decision 层不重新计算 suite，它读取 comparison 的 summary：

```python
comparison_summary = _dict(comparison.get("summary"))
```

然后 `_decision_summary()` 把这些字段带到最终 decision report：

```json
{
  "selected_suite_path": "builtin:standard-zh",
  "suite_consistency": "mixed",
  "suite_paths": ["builtin:standard-zh", "data/eval_prompts.json"],
  "suite_mismatch_count": 1
}
```

这里的职责边界很重要：

- comparison 决定 suite 是否一致。
- decision 只选择可执行候选，并保留 comparison 的 suite 解释。

如果 `suite_consistency=mixed`，recommendations 会出现：

```text
Compared runs use different benchmark suites; treat the selected run as execution triage, not a clean model-quality delta.
```

这句话是本版的核心约束：run decision 可以继续用于“下一步是否执行”，但不能被误读成模型能力结论。

## `src/minigpt/training_scale_run_decision_artifacts.py`

artifact 层把 suite 字段暴露到三种人工阅读面：

- CSV：新增 `selected_suite_path` 和 `suite_consistency`。
- Markdown：摘要区显示 selected suite 与 suite consistency。
- HTML：stats 卡片显示 suite path 和 consistency。

这些产物是只读证据，不参与选择策略。真正的选择仍来自 JSON 里的 `selected_run`、`rejected_runs` 和 `execute_command`。

## `src/minigpt/promoted_training_scale_comparison.py`

promoted comparison 复用普通 training scale comparison。v202 的关键是不要在 promoted 包装层丢失 suite 字段。

`_merge_comparison_rows()` 现在把内层 run 的：

```python
"suite_path": run.get("suite_path")
```

写回 promoted rows。这样 promoted input 表、CSV 和 HTML 都能看到每个 promoted run 的 suite。

`_summary()` 复制内层 comparison summary：

```json
{
  "suite_consistency": "mixed",
  "suite_path_count": 2,
  "suite_paths": ["builtin:standard-zh", "data/eval_prompts.json"],
  "suite_mismatch_count": 1
}
```

如果 promoted comparison 是 mixed suite，recommendations 会提醒审阅者先看 suite path，再判断 readiness delta 的含义。

## `src/minigpt/promoted_training_scale_comparison_artifacts.py`

promoted comparison artifact 层新增：

- CSV 的 `suite_path`。
- Markdown summary 的 `Suite consistency`。
- Markdown comparison 表的 `Suite` 列。
- HTML stats 的 suite consistency。
- HTML comparison 表的 suite path 列。

这让 promoted-only 报告不需要打开内层 `training_scale_run_comparison.json`，也能发现比较是否干净。

## `src/minigpt/promoted_training_scale_decision.py`

promoted baseline decision 从 promoted comparison 中读取 suite summary，并给 selected baseline 记录：

```json
"selected_suite_path": "builtin:standard-zh"
```

accepted 决策会追加建议：

```text
Carry `builtin:standard-zh` into the next promoted seed so later comparisons stay suite-consistent.
```

这与 v201 的 seed carryover 形成闭环：v201 负责“seed 能继承 suite”，v202 负责“decision 明确告诉 seed 应继承哪套 suite”。

## 测试覆盖

`tests/test_training_scale_run_comparison.py`

- 构造一个 default suite run 和一个 `standard-zh` run。
- 断言 comparison summary 为 `mixed`。
- 断言 `suite_mismatch_count=1`。
- 断言 delta 的 `suite_relation=changed`。
- 断言 recommendation 提醒 mixed suite 不能当作 clean quality delta。

`tests/test_training_scale_run_decision.py`

- 断言普通 decision 在 consistent suite 下带出 selected suite。
- 额外修改 comparison JSON 为 mixed suite，确认 decision 会继承 mixed summary，并输出风险提示。

`tests/test_promoted_training_scale_comparison.py`

- 构造 promoted comparison 中一条 default suite、一条 `standard-zh`。
- 断言 promoted summary 为 mixed。
- 断言 promoted row 保留 `suite_path=builtin:standard-zh`。

`tests/test_promoted_training_scale_decision.py`

- 断言 accepted promoted baseline decision 写出 `selected_suite_path=builtin:standard-zh`。

## 运行流程

典型链路如下：

```text
training_scale_run.json
 -> training_scale_run_comparison.json
    -> summary.suite_consistency
    -> baseline_deltas[].suite_relation
 -> training_scale_run_decision.json
    -> summary.selected_suite_path
    -> recommendations mixed-suite warning

promotion-index promoted inputs
 -> promoted_training_scale_comparison.json
    -> summary.suite_consistency
    -> promotions[].suite_path
 -> promoted_training_scale_decision.json
    -> summary.selected_suite_path
    -> recommendation for next seed
```

这条链路的重点不是“禁止不同 suite 的 run 同屏出现”，而是让同屏出现时必须标明证据边界。

## 证据边界

本版新增的 JSON/CSV/Markdown/HTML 都是最终审阅证据，但它们不训练模型、不执行 seed、不自动改写下一轮计划。

当 `suite_consistency=consistent` 时，readiness delta 更适合作为同基准治理对比。

当 `suite_consistency=mixed` 时，报告仍然能解释执行状态、gate 状态和候选选择，但不能用来声称模型质量提升。

当 `suite_consistency=missing` 时，说明旧 run 或外部 run 没有写 suite 字段，需要先回查 plan/batch summary。

## README 和截图闭环

README 更新了 v202 当前版本、tag、training scale workflow 能力描述，以及 `c/202` 截图说明。

`c/202/解释/说明.md` 记录每张截图证明的内容，图片目录保存聚焦测试、mixed suite smoke、promoted smoke、source encoding、全量 unittest 和文档检查结果。

## 一句话总结

v202 让 training scale 和 promoted baseline 链路不仅能传递 benchmark suite，还能在比较和决策时说明这次比较是否基于同一套 suite。

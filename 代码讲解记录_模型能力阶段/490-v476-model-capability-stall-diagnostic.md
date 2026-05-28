# v476：model capability stall diagnostic

## 本版目标和边界

v476 的目标是解释 v475 的关键现象：多 seed tiny ladder 中 validation loss 可以重复下降，但 benchmark score 和 generation flags 没有变化。v475 已经说明训练信号存在，v476 进一步把首尾 rung 的 prompt 级证据展开，判断停滞来自模型、数据、输出 token，还是 rubric 形态。

本版不重新训练模型，不新增外部评测集，也不声称模型能力提升。它只读取 v475 的归档产物，生成一个可复核的 case-level stall diagnostic。

## 前置能力

本版直接站在三层前置能力上：

- v473
  - 把 tiny baseline/candidate 的 loss delta 带入 eval loop。
- v474
  - 建立 `max_iters=1,2,4` 的单 seed capability ladder。
- v475
  - 将 ladder 跨 seed 复跑，确认 loss improvement 可重复，但 eval improvement 仍然为 0。

v476 不改变这些前置产物，只读取它们来做解释。

## 关键新增文件

- `src/minigpt/model_capability_stall_diagnostic.py`
  - 核心诊断逻辑。
  - 定位 `model_capability_ladder_stability.json`，读取 seed ladder report，解析首尾 rung 的 scorecard 和 generation-quality 产物。
- `src/minigpt/model_capability_stall_diagnostic_artifacts.py`
  - 输出 JSON/CSV/text/Markdown/HTML。
  - HTML 用于 Playwright 截图，CSV 用于逐 case 排查。
- `scripts/diagnose_model_capability_stall.py`
  - CLI 入口。
  - 输入可以是 stability JSON，也可以是 stability 输出目录。
- `tests/test_model_capability_stall_diagnostic.py`
  - 覆盖 token budget 阻塞、部分 rubric progress、缺失 ladder、artifact 输出、CLI `--require-pass` 失败返回码。

## 核心数据结构

最终报告是：

```text
model_capability_stall_diagnostic.json
```

关键字段：

- `summary`
  - 汇总所有 seed 和 case。
  - 包含 `score_improved_count`、`score_degraded_count`、`score_unchanged_count`、`persistent_fail_count`、`token_budget_or_shape_limit_count`。
- `seeds`
  - 每个 seed 一组诊断。
  - 记录首尾 `max_iters`、loss delta、score delta、generation flags delta。
- `cases`
  - 每个 seed 的每个 prompt 一行。
  - 对齐首尾 rung 的 `first_score`、`last_score`、`score_delta`、`last_failed_checks`、`last_missing_terms`、`first_preview`、`last_preview`。
- `interpretation`
  - 明确保留 `model_quality_claim=not_claimed`。
  - 给出下一步建议，而不是把诊断结论说成模型能力提升。

## 诊断规则

`stall_reason` 的判断顺序比较保守：

- 如果最后一档 case 已 pass，记为 `case_passed`。
- 如果最后一档仍有 `length_bounds` 或 `task_shape`，记为 `token_budget_or_shape_limit`。
- 如果分数提高但仍未 pass，记为 `partial_rubric_progress`。
- 如果输出预览也没变，记为 `generation_unchanged`。
- 如果仍缺 required terms，记为 `required_terms_missing`。
- 其他情况记为 `rubric_failure_persists`。

这个顺序故意优先暴露 token 和任务形态问题，因为 v474/v475 的 smoke 使用 `case-token-cap=4`，短输出会天然打不过许多 rubric 规则。

## v476 真实运行结果

本版读取：

```text
e/475/解释/model-capability-ladder-stability/model_capability_ladder_stability.json
```

真实输出：

```text
case_count=20
score_improved_count=0
score_degraded_count=0
score_unchanged_count=20
persistent_fail_count=20
token_budget_or_shape_limit_count=20
avg_score_delta=0.0
summary_decision=token_budget_or_shape_limits_block_eval_signal
```

这说明当前问题不是“多 seed 不稳定”，而是 tiny 输出太短，导致 prompt 级 rubric 仍被 `length_bounds`、`task_shape` 和 `must_include` 持续卡住。

## 测试覆盖

测试不是只看文件是否生成，而是覆盖了几类关键边界：

- token budget / task shape 持续失败时，summary 决策必须指向 `token_budget_or_shape_limits_block_eval_signal`。
- 当首尾分数提高但仍未 pass 时，case 层必须标记为 `partial_rubric_progress`。
- 当 seed ladder report 缺失时，诊断必须 fail，不能生成看似成功的空报告。
- JSON/CSV/text/Markdown/HTML 必须全部写出。
- CLI 在 `--require-pass` 下遇到失败输入必须返回 `1`。

## 运行证据

运行证据位于：

```text
e/476/解释/model-capability-stall-diagnostic/
e/476/图片/01-model-capability-stall-diagnostic.png
e/476/解释/playwright-model-capability-stall-diagnostic-snapshot.md
```

截图证明 HTML 报告可以在浏览器中审阅，snapshot 保留文本层证据。

## 一句话总结

v476 把“loss 降但 eval 不动”从总体指标拆到 prompt 级失败原因，明确下一步应先跑更长 token 的能力阶梯，再判断模型能力是否真的改善。

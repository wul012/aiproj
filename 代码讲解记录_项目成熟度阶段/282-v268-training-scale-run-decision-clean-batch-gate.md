# v268 training scale run decision clean batch gate

## 本版目标和边界

v268 的目标是给 training-scale run decision 增加一个可选的 clean batch-review gate。此前 run decision 会把 selected batch review/blocker context 写入 summary 和 recommendations，但默认仍允许 review-mode evidence 进入 `decision_status=review`，由人工判断是否继续执行。本版新增 `require_clean_batch_review`，让自动化场景可以要求 batch comparison review actions、blocker actions、maturity coverage regressions 都为 0，否则直接阻断 execute candidate。

本版不改变：

- 默认 run decision 行为；
- readiness score、baseline delta 和 candidate selection 排序；
- `require_gate_pass`、`require_batch_started`、`require_suite_consistency` 语义；
- execute command 生成方式；
- 下游 handoff/promotion 消费的既有字段。

## 前置链路

v253-v261 已经把 batch comparison review/blocker context 从 gated scale runs 带到 run comparison、run decision、handoff、promotion、promotion index、promoted comparison、promoted decision、promoted seed 和 seed handoff。v267 又把 run comparison 输出层拆出，降低后续维护压力。v268 回到功能增强：既然 batch review 风险已经能完整传递，就给 run decision 增加一个显式自动化开关，用于“只有干净 batch evidence 才能选出 execute command”的场景。

## 关键文件

### `src/minigpt/training_scale_run_decision.py`

新增参数：

```python
require_clean_batch_review: bool = False
```

当它为 `True` 时，`_clean_batch_review_reasons()` 会读取 comparison summary：

- `batch_comparison_blocker_action_count`
- `batch_comparison_review_action_count`
- `batch_maturity_coverage_regression_count`

只要其中任意一个大于 0，就把原因加入每个 run 的 rejection reasons，使 `selected_run=None`，`decision_status=blocked`。

新增 summary 字段：

- `require_clean_batch_review`
- `clean_batch_review_status`

`clean_batch_review_status` 的取值来自 `_clean_batch_review_status()`：

- `clean`：无 review、blocker、coverage regression；
- `review`：存在 review action 或 maturity coverage regression；
- `blocker`：存在 batch comparison blocker action。

### `scripts/decide_training_scale_run.py`

新增 CLI 参数：

```powershell
--require-clean-batch-review
```

这个参数只影响 run decision 的 candidate selection，不会自动执行训练。它适合 CI、release gate、自动化 handoff 等不希望人工 review evidence 进入 execute command 的场景。

### `src/minigpt/training_scale_run_decision_artifacts.py`

CSV、Markdown、HTML 都新增展示：

- `require_clean_batch_review`
- `clean_batch_review_status`

这样 JSON 之外的人读报告也能知道本次是否启用了 clean batch-review gate，以及当前 comparison 是 clean/review/blocker。

### `tests/test_training_scale_run_decision.py`

新增两类覆盖：

- 默认行为仍然是 `review`，开启 `require_clean_batch_review=True` 后同一份 comparison 变为 `blocked`；
- CSV/Markdown/HTML 都渲染新增字段，避免 JSON 有字段但人工报告缺失。

## 输入输出

输入仍然是 `training_scale_run_comparison.json` 或目录。新增输入选项是库参数和 CLI flag：

- Python: `require_clean_batch_review=True`
- CLI: `--require-clean-batch-review`

输出 report 新增：

```json
{
  "require_clean_batch_review": true,
  "summary": {
    "require_clean_batch_review": true,
    "clean_batch_review_status": "review"
  }
}
```

当 gate 被触发时，`rejected_runs[*].reasons` 会包含：

- `batch comparison blocker actions are present`
- `batch comparison review actions are present`
- `batch maturity coverage regressions are present`

## 测试覆盖

- 聚焦 run decision 和 workflow 测试覆盖默认 review 行为、strict clean batch gate 阻断、summary 字段和 artifact 渲染。
- CLI smoke 使用 `--require-clean-batch-review` 证明命令行会把 review evidence 阻断为非零退出。
- 全量 unittest 保护其他训练规模链路不受影响。
- source encoding 检查确认新增字段和文档没有编码/语法问题。

## 证据归档

运行截图和解释归档在 `c/268`：

- `c/268/图片/01-focused-tests.png`
- `c/268/图片/02-clean-batch-gate-smoke.png`
- `c/268/图片/03-full-unittest.png`
- `c/268/图片/04-source-encoding.png`
- `c/268/图片/05-docs-check.png`
- `c/268/解释/说明.md`

## 一句话总结

v268 把 batch review 风险从“可见的人工提醒”升级成“可选的自动化阻断条件”，让 run decision 能在需要干净执行证据时拒绝 review/blocker/coverage-regression comparison。

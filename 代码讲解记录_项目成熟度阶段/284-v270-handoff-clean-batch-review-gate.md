# v270 handoff clean batch review gate

## 本版目标和边界

v270 的目标是把 v269 workflow 层的 clean batch-review requirement 继续带到 training-scale execution handoff。此前 workflow 可以在 `--decision-require-clean-batch-review` 下阻断不干净的 batch review evidence，但 handoff 报告主要展示 selected batch review status，没有独立保留“上游是否要求 clean batch-review”以及“当前 clean status 是否满足要求”。本版让 handoff validation 能读到这条 requirement，并在执行前阻断不满足要求的 handoff。

本版不改变：

- 默认 workflow 和默认 handoff 行为；
- execute command 生成方式；
- selected batch review status 的旧字段；
- promotion、promotion index 和 promoted-only comparison 的输入路径；
- `--execute` 仍然只在 handoff allowed 后运行。

## 前置链路

v268 在 standalone run decision 层加入 `require_clean_batch_review`。v269 把同一开关接到 consolidated workflow。v270 继续往后补执行前边界：handoff 是从 reviewed command 走向真实执行的最后一层，因此它必须知道上游是否要求 clean batch-review evidence，不能只依赖人工从 workflow JSON 里回看。

## 关键文件

### `src/minigpt/training_scale_handoff.py`

新增 `_clean_batch_review_guard()`，从 nested decision summary、workflow summary 和 workflow 顶层字段读取：

- `decision_require_clean_batch_review`
- `require_clean_batch_review`
- `clean_batch_review_status`
- batch comparison review/blocker/regression 计数
- blocker reason list

`_handoff_allowed()` 新增 guard 参数。当 workflow 要求 clean batch-review 且 status 不是 `clean` 时，handoff 会返回 blocked：

```text
workflow requires clean batch-review evidence but status is not clean
```

summary 同步新增：

- `decision_require_clean_batch_review`
- `require_clean_batch_review`
- `clean_batch_review_status`

### `src/minigpt/training_scale_handoff_artifacts.py`

CSV、Markdown、HTML 都新增展示 clean batch-review guard 字段。这样 handoff 人工报告和机器 JSON 一致，不需要读者再跳回 workflow JSON 判断为什么被阻断。

### `scripts/execute_training_scale_handoff.py`

CLI 输出新增：

```text
clean_batch_review_status=<clean|review|blocker>
```

如果 handoff 因 clean batch-review requirement 被阻断，脚本仍然返回非零状态，用于 CI 或自动化前置检查。

### `tests/test_training_scale_handoff.py`

新增覆盖：

- handoff 能读取 workflow/decision 的 clean batch-review guard；
- requirement 未满足时 handoff 被阻断；
- CSV/Markdown/HTML 和 CLI stdout 都展示 `clean_batch_review_status`；
- 既有 suite guard、selected batch review、执行和 artifact writer 兼容测试继续保留。

## 输入输出

输入仍然是 `training_scale_workflow.json` 或 workflow 目录。新增消费字段来自 workflow/decision：

```json
{
  "decision_require_clean_batch_review": true,
  "clean_batch_review_status": "review"
}
```

输出 handoff report 新增：

```json
{
  "clean_batch_review_guard": {
    "decision_require_clean_batch_review": true,
    "clean_batch_review_status": "review"
  },
  "summary": {
    "handoff_status": "blocked",
    "decision_require_clean_batch_review": true,
    "clean_batch_review_status": "review"
  }
}
```

## 测试覆盖

- handoff 聚焦测试覆盖 clean batch-review guard 汇总、阻断、artifact 渲染和 CLI 输出。
- 全量 unittest 保护训练规模链路、治理报告、UI 和数据模块不受影响。
- source encoding hygiene 检查保证新增代码和文档没有 BOM 或语法错误。

## 证据归档

运行截图和解释归档在 `c/270`：

- `c/270/图片/01-focused-tests.png`
- `c/270/图片/02-handoff-clean-batch-gate-smoke.png`
- `c/270/图片/03-full-unittest.png`
- `c/270/图片/04-source-encoding.png`
- `c/270/图片/05-docs-check.png`
- `c/270/解释/说明.md`

## 一句话总结

v270 把 clean batch-review requirement 带到执行前 handoff 边界，让不满足 clean evidence 的 workflow 不能被误交接为可执行训练命令。
